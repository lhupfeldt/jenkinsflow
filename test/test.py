#!/usr/bin/env python

from __future__ import print_function

import sys, os, subprocess32 as subprocess, getpass, shutil
from docopt import docopt
from os.path import join as jp

import tenjin
from tenjin.helpers import *

here = os.path.abspath(os.path.dirname(__file__))

extra_sys_path = [os.path.normpath(path) for path in [here, jp(here, '../..'), jp(here, '../demo'), jp(here, '../demo/jobs')]]
sys.path = extra_sys_path + sys.path
os.environ['PYTHONPATH'] = ':'.join(extra_sys_path)


from jenkinsflow.test.framework import config
from jenkinsflow.test import cfg as test_cfg
from jenkinsflow.test.cfg import ApiType


_cache_dir = jp(os.path.dirname(here), '.cache')


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
        cov_rc_file.write(engine.render(jp(here, "coverage_rc.tenjin"), dict(api_type=api_type)))
            
    cmd = ['py.test', '--capture=sys', '--cov=' + here + '/..', '--cov-report=term-missing', '--cov-config=' + cov_rc_file_name, '--instafail', '--ff']
    try:
        if not parallel:
            return subprocess.check_call(cmd)
        subprocess.check_call(cmd + ['-n', '16'])        
    finally:
        if os.path.exists(_cache_dir):
            shutil.move(_cache_dir, api_type_cache_dir)
        os.unlink(cov_rc_file_name)


opts = """
Test jenkinsflow.
First runs all tests mocked in hyperspeed, then runs against Jenkins, using specialized_api, then run script_api jobs.

Usage:
test.py [--mock-speedup <speedup> --direct-url <direct_url> --pytest-args <pytest_args> --job-delete --skip-job-load <file>...]

General Options:
-s, --mock-speedup <speedup>     Time speedup when running mocked tests. int. [default: %(speedup_default)i]
--direct-url <direct_url>    Direct Jenkins URL. Must be different from the URL set in Jenkins (and preferably non proxied) [default: %(direct_url)s]
--pytest-args <pytest_args>  py.test arguments. str.

Job Load Options:  Control job loading and parallel test run. Specifying any of these options enables running of tests in parallel.
--job-delete       Don't delete and re-load jobs into Jenkins (assumes that re-loading generates correct job config).
                   Tests that require jobs to be deleted will delete the jobs regardless of this option
--skip-job-load    Don't load jobs into Jenkins (assumes all jobs already loaded and up to date).

<file>...  File names to pass to py.test
"""

def args_parser():
    test_cfg.select_api(ApiType.SPECIALIZED)
    doc = opts % dict(speedup_default=1000, direct_url=test_cfg.direct_url())
    args = docopt(doc, argv=None, help=True, version=None, options_first=False)

    speedup = float(args['--mock-speedup'])
    if speedup and speedup != 1:
        test_cfg.mock(speedup)
    if args['--direct-url']:
        os.environ[test_cfg.DIRECT_URL_NAME] = args['--direct-url']
    os.environ[test_cfg.SCRIPT_DIR_NAME] = test_cfg.script_dir()
    os.environ[test_cfg.SKIP_JOB_DELETE_NAME] = 'false' if args['--job-delete'] else 'true'
    os.environ[test_cfg.SKIP_JOB_LOAD_NAME] = 'true' if args['--skip-job-load'] else 'false'

    return args['--pytest-args'], args['<file>']


def start_msg(*msg):
    print("\n++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n", *msg)


def main():
    pytest_args, files = args_parser()

    print("Creating temporary test installation in", repr(config.pseudo_install_dir), "to make files available to Jenkins.")
    install_script = jp(here, 'tmp_install.sh')
    rc = subprocess.call([install_script])
    if rc:
        print("Failed test installation to. Install script is:", repr(install_script), file=sys.stderr)
        print("Warning: Some tests will fail!", file=sys.stderr)

    print("\nRunning tests")
    try:
        if False or pytest_args or files:
            extra_args = pytest_args.split(' ') + files if pytest_args else files
            subprocess.check_call(['py.test', '--capture=sys', '--instafail'] + extra_args)
            test_cfg.unmock()
            sys.exit(subprocess.call(['py.test', '--capture=sys', '--instafail'] + extra_args))

        run_tests(False, ApiType.MOCK)
        test_cfg.unmock()

        parallel = test_cfg.skip_job_load() | test_cfg.skip_job_delete()
        # TODO run all types in parallel, use extra job prefix and separate .cache
        run_tests(parallel, ApiType.SPECIALIZED)
        run_tests(parallel, ApiType.SCRIPT)

        start_msg("Testing setup.py")
        user = getpass.getuser()
        install_prefix = '/tmp/' + user
        tmp_packages_dir = install_prefix + '/lib/python2.7/site-packages'
        os.environ['PYTHONPATH'] = tmp_packages_dir
        if os.path.exists(tmp_packages_dir):
            shutil.rmtree(tmp_packages_dir)
        os.makedirs(tmp_packages_dir)
        subprocess.check_call([sys.executable, jp(here, '../setup.py'), 'install', '--prefix', install_prefix])
        shutil.rmtree(jp(here, '../build'))
    except Exception as ex:
        print('*** ERROR: There were errors! Check output! ***', repr(ex), file=sys.stderr)
        raise

    sys.exit(rc)


if __name__ == '__main__':
    main()
