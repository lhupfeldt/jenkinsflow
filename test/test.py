#!/usr/bin/python

from __future__ import print_function

import sys, os, imp, subprocess
from os.path import join as jp
here = os.path.abspath(os.path.dirname(__file__))

extra_sys_path = [os.path.normpath(path) for path in [jp(here, '../..'), jp(here, '../demo'), jp(here, '../demo/jobs'), jp(here, '../../jenkinsapi')]]
sys.path.extend(extra_sys_path)
os.environ['PYTHONPATH'] = ':'.join(extra_sys_path)
from jenkinsflow.flow import JobControlFailException

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
    visual_server_doc_dir = '/tmp/jenkinsflow'
    if not os.path.exists(visual_server_doc_dir):
        os.makedirs(visual_server_doc_dir)
    demo.main(api, visual_server_doc_dir)
    api.test_results()


def main():
    print("Running tests")
    if len(sys.argv) > 1:
        sys.exit(subprocess.call(['py.test', '--capture=sys', '--instafail'] + sys.argv[1:]))
    else:
        rc = subprocess.call(('py.test', '--capture=sys', '--cov=' + here + '/..', '--cov-report=term-missing', '--instafail', '--ff'))

    print("Validating demos")
    for demo in basic, hide_password, prefix:
        run_demo(demo)

    print("Validating demos with failing jobs")
    for demo in (errors,):
        try:
            run_demo(demo)
        except JobControlFailException as ex:
            print("Ok, got exception:", ex)
        else:
            raise Exception("Expected exception")

    if rc:
        print('*** ERROR: There were errors! Check output! ***', file=sys.stderr)
    sys.exit(rc)


if __name__ == '__main__':
    main()
