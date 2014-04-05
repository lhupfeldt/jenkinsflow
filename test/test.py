#!/usr/bin/env python

from __future__ import print_function

import sys, os, imp, subprocess, getpass, shutil
from os.path import join as jp
here = os.path.abspath(os.path.dirname(__file__))

extra_sys_path = [os.path.normpath(path) for path in [jp(here, '../..'), jp(here, '../demo'), jp(here, '../demo/jobs'), jp(here, '../../jenkinsapi')]]
sys.path = extra_sys_path + sys.path
os.environ['PYTHONPATH'] = ':'.join(extra_sys_path)
from jenkinsflow.flow import JobControlFailException, is_mocked
from jenkinsflow.test.framework import config

import basic, prefix, hide_password, errors


def run_demo(demo):
    print("\n\n")
    print("==== Demo:", demo.__name__, "====")
    job_load_module_name = demo.__name__ + '_jobs'
    job_load = imp.load_source(job_load_module_name, jp(here, '../demo/jobs', job_load_module_name + '.py'))
    print("-- loading jobs --")
    api = job_load.create_jobs()
    print()
    print("-- running jobs --")
    demo.main(api)
    api.test_results()


def main():
    print("Creating temporary test installation in", repr(config.pseudo_install_dir), "to make files available to Jenkins.")
    install_script = jp(here, 'tmp_install.sh')
    rc = subprocess.call([install_script])
    if rc:
        print("Failed test installation to. Install script is:", repr(install_script), file=sys.stderr)
        print("Warning: Some tests will fail!", file=sys.stderr)

    print("\nRunning tests")
    if len(sys.argv) > 1:
        sys.exit(subprocess.call(['py.test', '--capture=sys', '--instafail'] + sys.argv[1:]))
    else:
        skip_job_load = os.environ.get('JENKINSFLOW_SKIP_JOB_CREATE') == 'true'
        skip_job_delete = skip_job_load or os.environ.get('JENKINSFLOW_SKIP_JOB_DELETE') == 'true'
        if is_mocked or not skip_job_delete:
            rcfile = here + '/.coverage_mocked_rc'
            rc = subprocess.call(('py.test', '--capture=sys', '--cov=' + here + '/..', '--cov-report=term-missing', '--cov-config=' + rcfile, '--instafail', '--ff'))
        else:
            rcfile = here + '/.coverage_real_rc'
            rc = subprocess.call(('py.test', '--capture=sys', '--cov=' + here + '/..', '--cov-report=term-missing', '--cov-config=' + rcfile, '--instafail', '--ff', '-n', '8'))

    print("\nValidating demos")
    for demo in basic, hide_password, prefix:
        run_demo(demo)

    print("\nValidating demos with failing jobs")
    for demo in (errors,):
        try:
            run_demo(demo)
        except JobControlFailException as ex:
            print("Ok, got exception:", ex)
        else:
            raise Exception("Expected exception")

    print("\nTesting setup.py")
    user = getpass.getuser()
    install_prefix = '/tmp/' + user
    tmp_packages_dir = install_prefix + '/lib/python2.7/site-packages'
    os.environ['PYTHONPATH'] = tmp_packages_dir
    if os.path.exists(tmp_packages_dir):
        shutil.rmtree(tmp_packages_dir)
    os.makedirs(tmp_packages_dir)
    subprocess.check_call(['python', jp(here, '../setup.py'), 'install', '--prefix', install_prefix])

    if rc:
        print('*** ERROR: There were errors! Check output! ***', file=sys.stderr)
    sys.exit(rc)


if __name__ == '__main__':
    main()
