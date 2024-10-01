import os
import sys
import argparse
import errno
from pathlib import Path
from os.path import join as jp
import subprocess

import nox

sys.path.append('.')

from test.framework.cfg import ApiType, str_to_apis, dirs
from test.framework.nox_utils import cov_options_env, parallel_options
from test.framework.pytest_options import add_options

_HERE = Path(__file__).resolve().parent
_TEST_DIR = _HERE/"test"
_DEMO_DIR = _HERE/"demo"
_DOC_DIR = _HERE/"doc"

# Locally we have nox handle the different versions, but in each travis run there is only a single python which can always be found as just 'python'
_PY_VERSIONS = ["3.12", "3.11", "3.10", "3.9"] if not os.environ.get("TRAVIS_PYTHON_VERSION") else ["python"]
_IS_CI = os.environ.get("CI", "false").lower() == "true"


@nox.session(python=_PY_VERSIONS, reuse_venv=True)
def test(session):
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
    parsed_args = parser.parse_known_args(session.posargs)[0]
    # print("parsed_args:", parsed_args)
    apis = str_to_apis(parsed_args.api)
    # print("noxfile, apis:", apis)

    parallel = parsed_args.job_load or parsed_args.job_delete
    pytest_args.extend(parallel_options(parallel, apis))
    pytest_args.extend(["--capture=sys", "--instafail"])

    pytest_args.extend(session.posargs)

    try:
        os.makedirs(dirs.pseudo_install_dir)
    except OSError as ex:
        if ex.errno != errno.EEXIST:
            raise

    env = {}
    if apis != [ApiType.MOCK]:
        print(f"Creating venv test installation in '{dirs.pseudo_install_dir}' to make files available to Jenkins.")
        try:
            session.run(f"{session.bin}/python", "-m", "venv", "--symlinks", "--prompt=jenkinsflow-test-venv", dirs.pseudo_install_dir)
            python_executable = f"{dirs.pseudo_install_dir}/bin/python"
            session.run(python_executable, "-m", "pip", "install", "--upgrade", ".")
            env["JEKINSFLOW_TEST_JENKINS_API_PYTHON_EXECUTABLE"] = python_executable
            subprocess.check_call([_HERE/"test/tmp_install.sh", _TEST_DIR, jp(dirs.test_tmp_dir, "test")])
            subprocess.check_call([_HERE/"test/tmp_install.sh", _DEMO_DIR, jp(dirs.test_tmp_dir, "demo")])
        except:
            print(f"Failed venv test installation to '{dirs.pseudo_install_dir}'", file=sys.stderr)
            raise

    cov_file = _HERE/".coverage"
    if os.path.exists(cov_file):
        os.remove(cov_file)

    cov_opts, cov_env = cov_options_env(apis, True)
    env.update(cov_env)
    # env["COVERAGE_DEBUG"] = "config"
    session.run("pytest", "--capture=sys", *cov_opts, *pytest_args, env=env)


@nox.session(python=_PY_VERSIONS[0], reuse_venv=True)
def docs(session):
    session.install("--upgrade", ".", "-r", str(_DOC_DIR/"requirements.txt"))
    session.run("make", "-C", "doc/source", "html")


@nox.session(python=_PY_VERSIONS[0], reuse_venv=True)
def cli(session):
    session.install("--upgrade", ".")
    session.run("jenkinsflow", "set-build-description", "--help")
