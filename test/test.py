#!/usr/bin/env python

"""
Test jenkinsflow.
"""

from __future__ import print_function

import sys, os, getpass, shutil
major_version = sys.version_info.major
if major_version < 3:
    import subprocess32 as subprocess
else:
    import subprocess
from os.path import join as jp

import click
import tenjin
from tenjin.helpers import *

try:
    import pytest
except ImportError:
    print("See setup.py for test requirements, or use 'python setup.py test'", file=sys.stderr)
    raise

here = os.path.abspath(os.path.dirname(__file__))
top_dir = os.path.dirname(here)

extra_sys_path = [os.path.normpath(path) for path in [here, jp(top_dir, '..'), jp(top_dir, 'demo'), jp(top_dir, 'demo/jobs')]]
sys.path = extra_sys_path + sys.path
os.environ['PYTHONPATH'] = ':'.join(extra_sys_path)

from jenkinsflow.test.framework import config
from jenkinsflow.test import cfg as test_cfg
from jenkinsflow.test.cfg import ApiType

from jenkinsflow import hyperspeed


def dummy(*_args):
    print("*** Please use test/tests.py to run tests", file=sys.stderr)


class TestLoader(object):
    def loadTestsFromNames(self, names, module=None):
        return dummy


test_cfg.select_api(ApiType.JENKINS)
_cache_dir = jp(top_dir, '.cache')


def _pytest(args):
    rc = pytest.main(args)
    if rc:
        sys.exit(rc)
    return rc


def run_tests(parallel, api_type):
    start_msg("Using " + str(api_type))

    # Running the test suite multiple times (for each api) breaks the run failed first, preserve the cache dir for each type
    api_type_cache_dir = _cache_dir + '-' + api_type.name
    if os.path.exists(api_type_cache_dir):
        if os.path.exists(_cache_dir):
            shutil.rmtree(_cache_dir)
        shutil.move(api_type_cache_dir, _cache_dir)

    test_cfg.select_api(api_type)

    engine = tenjin.Engine()
    cov_rc_file_name = jp(here, '.coverage_rc_' +  api_type.env_name().lower())
    with open(cov_rc_file_name, 'w') as cov_rc_file:
        cov_rc_file.write(engine.render(jp(here, "coverage_rc.tenjin"), dict(api_type=api_type, top_dir=top_dir)))

    args = ['--capture=sys', '--cov=' + top_dir, '--cov-report=term-missing', '--cov-config=' + cov_rc_file_name, '--instafail', '--ff']
    try:
        if not parallel:
            if api_type == ApiType.MOCK:
                return _pytest(args)
            else:
                # Note: 'boxed' is required for the kill/abort_current test not to abort other tests
                return _pytest(args + ['--boxed'])
        _pytest(args + ['--boxed', '-n', '16'])
    finally:
        if os.path.exists(_cache_dir):
            shutil.move(_cache_dir, api_type_cache_dir)
        os.unlink(cov_rc_file_name)


def start_msg(*msg):
    print("\n++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n", *msg)


@click.command()
@click.option('--mock-speedup', '-s', help="Time speedup when running mocked tests.", default=1000)
@click.option('--direct-url', help="Direct Jenkins URL. Must be different from the URL set in Jenkins (and preferably non proxied)", default=test_cfg.direct_url())
@click.option('--pytest-args', help="py.test arguments.")
@click.option('--job-delete/--no-job-delete', help="Delete and re-load jobs into Jenkins. Default is --no-job-delete.", default=False)
@click.option('--job-load/--no-job-load', help="Load jobs into Jenkins (skipping job load assumes all jobs already loaded and up to date). Deafult is --job-load.", default=True)
@click.argument('testfile', nargs=-1, type=click.Path(exists=True, readable=True))
def cli(mock_speedup, direct_url, pytest_args, job_delete, job_load, testfile):
    """
    Test jenkinsflow.
    First runs all tests mocked in hyperspeed, then runs against Jenkins, using jenkins_api, then run script_api jobs.

    Normally jobs will be run in parallel, specifying --job-delete disables this.
    The default options assumes that re-loading without deletions generates correct job config.
    Tests that require jobs to be deleted/non-existing will delete the jobs, regardless of the --job-delete option.

    [TESTFILE]... File names to pass to py.test
    """

    hyperspeed.set_speedup(mock_speedup)
    os.environ[test_cfg.DIRECT_URL_NAME] = direct_url
    os.environ[test_cfg.SKIP_JOB_DELETE_NAME] = 'false' if job_delete else 'true'
    os.environ[test_cfg.SKIP_JOB_LOAD_NAME] = 'false' if job_load else 'true'
    os.environ[test_cfg.SCRIPT_DIR_NAME] = test_cfg.script_dir()

    print("Creating temporary test installation in", repr(config.pseudo_install_dir), "to make files available to Jenkins.")
    install_script = jp(here, 'tmp_install.sh')
    rc = subprocess.call([install_script])
    if rc:
        print("Failed test installation to", repr(config.pseudo_install_dir), "Install script is:", repr(install_script), file=sys.stderr)
        print("Warning: Some tests will fail!", file=sys.stderr)

    cov_file = ".coverage"
    for cov_file in jp(here, cov_file), jp(top_dir, cov_file):
        if os.path.exists(cov_file):
            os.remove(cov_file)

    print("\nRunning tests")
    try:
        if pytest_args or testfile:
            extra_args = pytest_args.split(' ') + list(testfile) if pytest_args else list(testfile)
            _pytest(['--capture=sys', '--instafail'] + extra_args)
            hyperspeed.set_speedup(1)
            test_cfg.select_api(ApiType.JENKINS)
            _pytest(['--capture=sys', '--instafail'] + extra_args)
            test_cfg.select_api(ApiType.SCRIPT)
            sys.exit(_pytest(['--capture=sys', '--instafail'] + extra_args))

        run_tests(False, ApiType.MOCK)
        hyperspeed.set_speedup(1)

        hudson = os.environ.get('HUDSON_URL')
        if hudson:
            print("Disabling parallel run, Hudson can't handle it :(")
        parallel = test_cfg.skip_job_load() or test_cfg.skip_job_delete() and not hudson
        # TODO run all types in parallel, use extra job prefix and separate .cache
        run_tests(parallel, ApiType.JENKINS)
        run_tests(True, ApiType.SCRIPT)

        start_msg("Testing setup.py")
        user = getpass.getuser()
        install_prefix = '/tmp/' + user
        tmp_packages_dir = install_prefix + '/lib/python{major}.{minor}/site-packages'.format(major=major_version, minor=sys.version_info.minor)
        os.environ['PYTHONPATH'] = tmp_packages_dir
        if os.path.exists(tmp_packages_dir):
            shutil.rmtree(tmp_packages_dir)
        os.makedirs(tmp_packages_dir)

        os.chdir(top_dir)
        subprocess.check_call([sys.executable, jp(top_dir, 'setup.py'), 'install', '--prefix', install_prefix])
        shutil.rmtree(jp(top_dir, 'build'))

        start_msg("Testing documentation generation")

        os.chdir('doc/source')
        subprocess.check_call(['make', 'html'])
    except Exception as ex:
        print('*** ERROR: There were errors! Check output! ***', repr(ex), file=sys.stderr)
        raise

    sys.exit(rc)


if __name__ == '__main__':
    cli()  # pylint: disable=no-value-for-parameter
