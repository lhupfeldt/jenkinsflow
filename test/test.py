#!/usr/bin/python

from __future__ import print_function

import sys, os, imp
from os.path import join as jp
here = os.path.abspath(os.path.dirname(__file__))

sys.path.extend([jp(here, '../..'), jp(here, '../demo'), jp(here, '../demo/jobs'), jp(here, '../../jenkinsapi')])
from jenkinsflow.jobcontrol import JobControlFailException

import basic, prefix, hide_password, errors
import single_level, multi_level_mixed, no_args, single_level_errors, invoke_unchecked, empty_flow, boolean_int_params, hide_password_fail, multi_level_errors1


def run_demo(demo):
    print("\n\n")
    print("==== Demo:", demo.__name__, "====")
    job_load_module_name = demo.__name__ + '_jobs'
    job_load = imp.load_source(job_load_module_name, jp('../demo/jobs', job_load_module_name + '.py'))
    print("-- loading jobs --")
    api = job_load.create_jobs()
    print()
    print("-- running jobs --")
    demo.main(api)
    api.test_results()


def main():
    os.chdir(here)

    print("Runnning tests")
    for test in hide_password_fail, single_level, single_level_errors, invoke_unchecked, empty_flow, no_args, multi_level_mixed, boolean_int_params, multi_level_errors1:
        print("\n\n")
        print("==== Test:", test.__name__, "====")
        test.main()

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


if __name__ == '__main__':
    main()

