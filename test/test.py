#!/usr/bin/env python

from __future__ import print_function

import sys, os, imp, subprocess, getpass, shutil
from os.path import join as jp
here = os.path.abspath(os.path.dirname(__file__))

extra_sys_path = [os.path.normpath(path) for path in [jp(here, '../..'), jp(here, '../demo'), jp(here, '../demo/jobs'), jp(here, '../../jenkinsapi')]]
sys.path = extra_sys_path + sys.path
os.environ['PYTHONPATH'] = ':'.join(extra_sys_path)

from jenkinsflow.flow import JobControlFailException

from jenkinsflow.test.framework import config
from jenkinsflow.test import test_cfg

import basic, calculated_flow, prefix, hide_password, errors


def run_demo(demo, execute_script=False):
    print("\n\n")
    print("==== Demo:", demo.__name__, "====")
    job_load_module_name = demo.__name__ + '_jobs'
    job_load = imp.load_source(job_load_module_name, jp(here, '../demo/jobs', job_load_module_name + '.py'))
    print("-- loading jobs --")
    api = job_load.create_jobs()
    print()
    if not execute_script:
        print("-- running jobs --")
        demo.main(api)
        api.test_results()
    else:
        print("-- running demo script --")
        subprocess.check_call([sys.executable, demo.__file__.replace('.pyc', '.py')])


def validate_all_demos(execute_script=False):
    print("\nValidating demos")
    for demo in basic, calculated_flow, hide_password, prefix:
        run_demo(demo, execute_script)

    print("\nValidating demos with failing jobs")
    for demo in (errors,):
        try:
            run_demo(demo, execute_script)
        except (JobControlFailException, subprocess.CalledProcessError) as ex:
            print("Ok, got exception:", ex)
        else:
            raise Exception("Expected exception")


def run_tests(parallel, cov_rc_file):
    cmd = ['py.test', '--capture=sys', '--cov=' + here + '/..', '--cov-report=term-missing', '--cov-config=' + cov_rc_file, '--instafail', '--ff']
    if not parallel:
        return subprocess.check_call(cmd)
    return subprocess.check_call(cmd + ['-n', '16'])


def main():
    print("Creating temporary test installation in", repr(config.pseudo_install_dir), "to make files available to Jenkins.")
    install_script = jp(here, 'tmp_install.sh')
    rc = subprocess.call([install_script])
    if rc:
        print("Failed test installation to. Install script is:", repr(install_script), file=sys.stderr)
        print("Warning: Some tests will fail!", file=sys.stderr)

    print("\nRunning tests")
    try:
        if len(sys.argv) > 1:
            sys.exit(subprocess.call(['py.test', '--capture=sys', '--instafail'] + sys.argv[1:]))
        
        test_cfg.mock_default()
        run_tests(False, here + '/.coverage_mocked_rc')
        validate_all_demos()
        
        test_cfg.unmock()
        parallel = test_cfg.skip_job_load() | test_cfg.skip_job_delete()
        if test_cfg.use_jenkinsapi():
            run_tests(parallel, here + '/.coverage_jenkinsapi_rc')
        else:
            run_tests(parallel, here + '/.coverage_real_rc')
        validate_all_demos(execute_script=True)
        
        print("\nTesting setup.py")
        user = getpass.getuser()
        install_prefix = '/tmp/' + user
        tmp_packages_dir = install_prefix + '/lib/python2.7/site-packages'
        os.environ['PYTHONPATH'] = tmp_packages_dir
        if os.path.exists(tmp_packages_dir):
            shutil.rmtree(tmp_packages_dir)
        os.makedirs(tmp_packages_dir)
        subprocess.check_call([sys.executable, jp(here, '../setup.py'), 'install', '--prefix', install_prefix])
    except:
        print('*** ERROR: There were errors! Check output! ***', file=sys.stderr)
        raise

    sys.exit(rc)


if __name__ == '__main__':
    main()
