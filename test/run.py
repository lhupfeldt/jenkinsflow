#!/usr/bin/env python

"""
Test jenkinsflow.
"""

import sys, copy, errno, os
from os.path import join as jp
import subprocess

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


def run_tests(parallel, api_types, args, coverage=True, mock_speedup=1):
    args = copy.copy(args)

    test_cfg.select_speedup(mock_speedup)

    if coverage:
        engine = tenjin.Engine()

        if len(api_types) == 3:
            fail_under = 95
        elif ApiType.JENKINS in api_types:
            fail_under = 94
        elif ApiType.MOCK in api_types and ApiType.SCRIPT in api_types:
            fail_under = 90
        elif ApiType.MOCK in api_types:
            fail_under = 88
        else:
            fail_under = 86

        # Note: cov_rc_file_name hardcoded in .travis.yml
        cov_rc_file_name = jp(here, '.coverage_rc_' +  '_'.join(api_type.name.lower() for api_type in api_types))
        with open(cov_rc_file_name, 'w') as cov_rc_file:
            context = dict(api_types=api_types, top_dir=top_dir, fail_under=fail_under)
            cov_rc_file.write(engine.render(jp(here, "coverage_rc.tenjin"), context))
            args.extend(['--cov=' + top_dir, '--cov-report=term-missing', '--cov-config=' + cov_rc_file_name])

    if api_types != [ApiType.MOCK]:
        # Note: 'boxed' is required for the kill/abort_current test not to abort other tests
        args.append('--boxed')

        if parallel:
            args.extend(['-n', '16'])

    print('pytest.main', args)
    rc = pytest.main(args)
    if rc:
        raise Exception("pytest {args} failed with code {rc}".format(args=args, rc=rc))


def start_msg(*msg):
    print("\n++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n", *msg)


def cli(mock_speedup=1000,
        direct_url=test_cfg.direct_url(test_cfg.ApiType.JENKINS),
        apis=None,
        pytest_args=None,
        job_delete=False,
        job_load=True,
        testfile=None):
    """
    Test jenkinsflow.
    First runs all tests mocked in hyperspeed, then runs against Jenkins, using jenkins_api, then run script_api jobs.

    Normally jobs will be run in parallel, specifying --job-delete disables this.
    The default options assumes that re-loading without deletions generates correct job config.
    Tests that require jobs to be deleted/non-existing will delete the jobs, regardless of the --job-delete option.

    [TESTFILE]... File names to pass to py.test
    """

    os.environ[test_cfg.DIRECT_URL_NAME] = direct_url
    os.environ[test_cfg.SKIP_JOB_DELETE_NAME] = 'false' if job_delete else 'true'
    os.environ[test_cfg.SKIP_JOB_LOAD_NAME] = 'false' if job_load else 'true'

    args = ['--capture=sys', '--instafail']

    if apis is None:
        api_types = [ApiType.MOCK, ApiType.SCRIPT, ApiType.JENKINS]
    else:
        api_types = [ApiType[api_name.strip().upper()] for api_name in apis.split(',')]
    args.extend(['-k', ' or '.join([apit.name for apit in api_types])])

    rc = 0
    target_dir = "/tmp/jenkinsflow-test/jenkinsflow"
    try:
        os.makedirs(target_dir)
    except OSError as ex:
        if ex.errno != errno.EEXIST:
            raise

    if api_types != [ApiType.MOCK]:
        print("Creating temporary test installation in", repr(config.pseudo_install_dir), "to make files available to Jenkins.")
        install_script = jp(here, 'tmp_install.sh')
        rc = subprocess.call([install_script, target_dir])
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
            coverage = False
            args.extend(pytest_args.split(' ') + list(testfile) if pytest_args else list(testfile))
        else:
            coverage = True
            args.append('--ff')

        hudson = os.environ.get('HUDSON_URL')
        if hudson:
            print("Disabling parallel run, Hudson can't handle it :(")
        parallel = test_cfg.skip_job_load() or test_cfg.skip_job_delete() and not hudson
        run_tests(parallel, api_types, args, coverage, mock_speedup)

        if not testfile and os.environ.get('CI', 'false').lower() != 'true':
            # This is automatically tested by readdthedocs, so no need to test on Travis
            start_msg("Testing documentation generation")

            os.chdir(jp(top_dir, 'doc/source'))
            del os.environ['PYTHONPATH']
            subprocess.check_call(['make', 'html'])
    except Exception as ex:
        print('*** ERROR: There were errors! Check output! ***', repr(ex), file=sys.stderr)
        raise

    sys.exit(rc)


@click.command()
@click.option('--mock-speedup', '-s', help="Time speedup when running mocked tests.", default=1000)
@click.option('--direct-url', help="Direct Jenkins URL. Must be different from the URL set in Jenkins (and preferably non proxied)",
              default=test_cfg.direct_url(test_cfg.ApiType.JENKINS))
@click.option('--apis', help="Select which api(s) to use/test. Comma separated list. Possible values: 'jenkins, 'script', 'mock'. Default is all.", default=None)
@click.option('--pytest-args', help="py.test arguments.")
@click.option('--job-delete/--no-job-delete', help="Delete and re-load jobs into Jenkins. Default is --no-job-delete.", default=False)
@click.option('--job-load/--no-job-load', help="Load jobs into Jenkins (skipping job load assumes all jobs already loaded and up to date). Deafult is --job-load.", default=True)
@click.argument('testfile', nargs=-1, type=click.Path(exists=True, readable=True))
def _cli(mock_speedup, direct_url, apis, pytest_args, job_delete, job_load, testfile):
    cli(mock_speedup, direct_url, apis, pytest_args, job_delete, job_load, testfile)


if __name__ == '__main__':
    _cli()  # pylint: disable=no-value-for-parameter
