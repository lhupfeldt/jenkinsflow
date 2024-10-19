"""nox https://nox.thea.codes/en/stable/ configuration"""

# Use nox >= 2023.4.22

import os
import sys
import argparse
import errno
import glob
from pathlib import Path
import subprocess
from typing import Sequence

import nox


_HERE = Path(__file__).absolute().parent
_TEST_DIR = _HERE/"test"
_DEMO_DIR = _HERE/"demo"
_DOC_DIR = _HERE/"doc"

sys.path.extend((str(_HERE), str(_DEMO_DIR)))

from test.framework.cfg import ApiType, str_to_apis, dirs
from test.framework.pytest_options import add_options


# Locally we have nox handle the different versions, but in each travis run there is only a single python which can always be found as just 'python'
_PY_VERSIONS = ["3.12", "3.11", "3.10", "3.9"] if not os.environ.get("TRAVIS_PYTHON_VERSION") else ["python"]
_IS_CI = os.environ.get("CI", "false").lower() == "true"

nox.options.error_on_missing_interpreters = True


def _cov_options_env(api_types: Sequence[ApiType], env: dict[str, str], fail_under: int = 0) -> Sequence[str]:
    """Setup coverage options.

    Return pytest coverage options, and env variables dict.
    """

    if not fail_under:
        if len(api_types) == 3:
            fail_under = 93.9
        elif ApiType.JENKINS in api_types:
            fail_under = 95
        elif ApiType.MOCK in api_types and ApiType.SCRIPT in api_types:
            fail_under = 90
        elif ApiType.MOCK in api_types:
            fail_under = 84.77
        elif ApiType.SCRIPT in api_types:
            fail_under = 81.66
        else:
            raise ValueError(f"Unknown coverage requirement for api type combination: {api_types}")

    # Set coverage exclude lines based on selected API types
    api_exclude_lines = []
    if api_types == [ApiType.SCRIPT]:
        # Parts of api_base not used in script_api (overridden methods)
        api_exclude_lines.append(r"return (self.job.public_uri + '/' + repr(self.build_number) + '/console')")

    # Set coverage exclude files based on selected API type
    api_exclude_files = []
    if ApiType.JENKINS not in api_types:
        api_exclude_files.append("jenkins_api.py")
    if ApiType.SCRIPT not in api_types:
        api_exclude_files.append("script_api.py")

    env["COV_API_EXCLUDE_LINES"] = "\n".join(api_exclude_lines)
    env["COV_API_EXCLUDE_FILES"] = "\n".join(api_exclude_files)

    return ['--cov', '--cov-report=term-missing', f'--cov-fail-under={fail_under}', f'--cov-config={_TEST_DIR/".coveragerc"}']


def _pytest_parallel_options(parallel, api_types):
    args = []

    if api_types != [ApiType.MOCK]:
        # Note: 'forked' is required for the kill/abort_current test not to abort other tests
        args.append('--forked')

        # Note: parallel actually significantly slows down the test when only running mock
        if parallel:
            args.extend(['-n', '16'])

    return args


# @nox.session(python=_PY_VERSIONS, reuse_venv=True)
# def typecheck(session):
#     session.install("-e", ".", "mypy>=1.5.1")
#     session.run("mypy", str(_HERE/"src"))


# TODO: pylint-pytest does not support 3.12
@nox.session(python="3.11", reuse_venv=True)
def pylint(session):
    session.install(".", "pylint>=3.3.1", "pylint-pytest>=1.1.8")

    print("\nPylint src")
    session.run("pylint", "--fail-under", "8.1", str(_HERE/"src"))

    print("\nPylint test sources")
    disable_checks = "missing-module-docstring,missing-class-docstring,missing-function-docstring"
    disable_checks += ",multiple-imports,invalid-name,duplicate-code"
    session.run(
        "pylint", "--fail-under", "9.1", "--variable-rgx", r"[a-z_][a-z0-9_]{1,30}$", "--disable", disable_checks,
        "--ignore", "jenkins_security.py,demos_test.py", str(_TEST_DIR))


@nox.session(python=_PY_VERSIONS, reuse_venv=True)
def unit(session):
    """
    Test jenkinsflow.
    Runs all tests mocked in hyperspeed, runs against Jenkins, using jenkins_api, and run script_api jobs.

    Normally jobs will be run in parallel, specifying 'job_delete' disables this.
    The default options assumes that re-loading without deletions generates correct job config.
    Tests that require jobs to be deleted/non-existing will delete the jobs, regardless of the 'job_delete' option.

    Will process some of the special pytest args:
        direct_url: Direct Jenkins URL. Must be different from the URL set in Jenkins (and preferably non proxied).
        apis: The apis totest, default all.
        job_delete: Delete and re-load jobs into Jenkins.
        job_load: Load jobs into Jenkins (skipping job load assumes all jobs already loaded and up to date).
    """

    session.install("--upgrade", ".", "-r", str(_TEST_DIR/"requirements.txt"))

    pytest_args = []
    if _IS_CI:
        pytest_args.append("-vvv")

    parser = argparse.ArgumentParser(description="Process pytest options")
    add_options(parser)
    parsed_args = parser.parse_known_args(session.posargs)
    # print("parsed_args:", parsed_args)
    special_args = parsed_args[0]
    unknown_pytest_args = parsed_args[1]

    apis = str_to_apis(special_args.api)
    # print("noxfile, apis:", apis)

    cov_file = _HERE/".coverage"
    if os.path.exists(cov_file):
        os.remove(cov_file)

    env = {}

    # If we have unknow pytest options we don't know what the coverage would be
    fail_under = 1 if unknown_pytest_args else 0
    cov_opts = _cov_options_env(apis, env, fail_under)
    # env["COVERAGE_DEBUG"] = "config,trace,pathmap"

    parallel = special_args.job_load or special_args.job_delete
    pytest_args.extend(_pytest_parallel_options(parallel, apis))
    pytest_args.extend(["--capture=sys", "--instafail", "-p", "no:warnings" "--failed-first"])
    pytest_args.extend(session.posargs)

    try:
        os.makedirs(dirs.pseudo_install_dir)
    except OSError as ex:
        if ex.errno != errno.EEXIST:
            raise

    if apis != [ApiType.MOCK]:
        print(f"Creating venv test installation in '{dirs.pseudo_install_dir}' to make files available to Jenkins.")
        try:
            session.run(f"{session.bin}/python", "-m", "venv", "--symlinks", "--prompt=jenkinsflow-test-venv", dirs.pseudo_install_dir)
            python_executable = f"{dirs.pseudo_install_dir}/bin/python"
            session.run(python_executable, "-m", "pip", "install", "--upgrade", ".")
            env["JEKINSFLOW_TEST_JENKINS_API_PYTHON_EXECUTABLE"] = python_executable
            tmp_inst_script = _HERE/"test/framework/tmp_install.sh"
            subprocess.check_call([tmp_inst_script, _TEST_DIR, f"{dirs.test_tmp_dir}/test"])
            subprocess.check_call([tmp_inst_script, _DEMO_DIR, f"{dirs.test_tmp_dir}/demo"])
        except:
            print(f"Failed venv test installation to '{dirs.pseudo_install_dir}'", file=sys.stderr)
            raise

    session.run("pytest", "--capture=sys", *cov_opts, *pytest_args, env=env)


@nox.session(python=_PY_VERSIONS[0], reuse_venv=True)
def build(session):
    session.install("build>=1.0.3", "twine>=4.0.2")
    for ff in glob.glob("dist/*"):
        os.remove(ff)
    session.run("python", "-m", "build")
    session.run("python", "-m", "twine", "check", "dist/*")


@nox.session(python=_PY_VERSIONS[0], reuse_venv=True)
def docs(session):
    session.install("--upgrade", ".", "-r", str(_DOC_DIR/"requirements.txt"))
    session.run("make", "-C", "doc/source", "html")


@nox.session(python=_PY_VERSIONS[0], reuse_venv=True)
def cli(session):
    session.install("--upgrade", ".")
    session.run("jenkinsflow", "set-build-description", "--help")
