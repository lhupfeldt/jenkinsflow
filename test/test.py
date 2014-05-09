#!/usr/bin/env python

from __future__ import print_function

import sys, os, imp, subprocess, getpass, shutil, argparse
from os.path import join as jp
here = os.path.abspath(os.path.dirname(__file__))

extra_sys_path = [os.path.normpath(path) for path in [here, jp(here, '../..'), jp(here, '../demo'), jp(here, '../demo/jobs'), jp(here, '../../jenkinsapi')]]
sys.path = extra_sys_path + sys.path
os.environ['PYTHONPATH'] = ':'.join(extra_sys_path)

from jenkinsflow.flow import JobControlFailException

from jenkinsflow.test.framework import config
from jenkinsflow.test import cfg as test_cfg
from jenkinsflow.test.cfg import env_var_prefix


def run_tests(parallel, cov_rc_file):
    cmd = ['py.test', '--capture=sys', '--cov=' + here + '/..', '--cov-report=term-missing', '--cov-config=' + cov_rc_file, '--instafail', '--ff']
    if not parallel:
        return subprocess.check_call(cmd)
    return subprocess.check_call(cmd + ['-n', '16'])


def args_parser():
    speedup_default = 1000
    test_cfg.mock(speedup_default)

    class EnvAction(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            name = env_var_prefix + self.dest.replace('-', '_').upper()
            value = 'true' if self.nargs == 0 and not values else values
            if value == '':
                raise argparse.ArgumentError(self, "'' is not a valid value")
            # print("Env:", self, parser, namespace, name, value, option_string)
            os.environ[name] = str(value)
            setattr(namespace, self.dest, value)

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     description='Test jenkinsflow. First runs all tests mocked in hyperspeed, then runs against Jenkins.')
    parser.add_argument('--mock-speedup', type=int, default=speedup_default, action=EnvAction, help='Time speedup when running mocked tests')
    parser.add_argument('--direct-url', default=test_cfg.direct_url(), action=EnvAction,
                        help='Direct Jenkins URL. Must be different from the URL set in Jenkins (and preferably non proxied)')
    parser.add_argument('--use-jenkinsapi', nargs=0, action=EnvAction,
                        help="Use 'jenkinsapi_wrapper' module for Jenkins access, instead of 'specialized_api'.")
    parser.add_argument('--pytest-args', default=None, help="String of py.test arguments")

    jlg = parser.add_argument_group('Job Load', 'Control job loading and parallel test run. Specifying any of these options enables running of tests in parallel.')
    jlg.add_argument('--skip-job-delete', nargs=0, action=EnvAction, help="Don't delete and re-load jobs into Jenkins (assumes already loaded and up to date).")
    jlg.add_argument('--skip-job-load', nargs=0, action=EnvAction, help="Don't load jobs into Jenkins (assumes already loaded and up to date).")

    parser.add_argument('files', default=None, nargs='*', help="File names to pass to py.test")
    return parser


def main():
    args = args_parser().parse_args()
    print("Creating temporary test installation in", repr(config.pseudo_install_dir), "to make files available to Jenkins.")
    install_script = jp(here, 'tmp_install.sh')
    rc = subprocess.call([install_script])
    if rc:
        print("Failed test installation to. Install script is:", repr(install_script), file=sys.stderr)
        print("Warning: Some tests will fail!", file=sys.stderr)

    print("\nRunning tests")
    try:
        if False or args.pytest_args or args.files:
            extra_args = args.pytest_args.split(' ') + args.files if args.pytest_args else args.files
            subprocess.check_call(['py.test', '--capture=sys', '--instafail'] + extra_args)
            test_cfg.unmock()
            sys.exit(subprocess.call(['py.test', '--capture=sys', '--instafail'] + extra_args))

        run_tests(False, here + '/.coverage_mocked_rc')

        test_cfg.unmock()
        parallel = test_cfg.skip_job_load() | test_cfg.skip_job_delete()
        if test_cfg.use_jenkinsapi():
            print("Using jenkinsapi_wrapper")
            run_tests(parallel, here + '/.coverage_jenkinsapi_rc')
        else:
            print("Using specialized_api")
            run_tests(parallel, here + '/.coverage_real_rc')

        print("\nTesting setup.py")
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
