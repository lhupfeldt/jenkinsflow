#!/usr/bin/python

from __future__ import print_function

import sys, os, imp
from os.path import join as jp
here = os.path.abspath(os.path.dirname(__file__))

sys.path.extend([jp(here, '../..'), jp(here, '../demo'), jp(here, '../../jenkinsapi')])
from jenkinsflow.jobcontrol import JobControlFailException

from framework.mock_api import is_mocked

import nested, single_level, prefix, hide_password
import multi_level_errors1, multi_level_errors2

import multi_level_mixed, no_args, single_level_errors, invoke_unchecked, empty_flow, boolean_int_params

os.chdir(here)

def run_demo(demo):
    print("")
    print("==== Demo:", demo.__name__, "====")
    job_load_module_name = demo.__name__ + '_jobs'
    job_load = imp.load_source(job_load_module_name, jp('../demo', job_load_module_name+ '.py'))
    print("-- loading jobs --")
    job_load.main()
    print
    print("-- running jobs --")
    demo.main()


print("Runnning tests")
for test in single_level_errors, invoke_unchecked, empty_flow, no_args, multi_level_mixed, boolean_int_params:
    print("")
    print("==== Test:", test.__name__, "====")
    test.main()

# TODO: allow running demos mocked
if is_mocked():
    sys.exit(0)

print("Validating demos")
for demo in nested, single_level, prefix:
    run_demo(demo)

print("Validating demos with failing jobs")
for demo in hide_password, multi_level_errors1, multi_level_errors2:
    try:
        run_demo(demo)
    except JobControlFailException as ex:
        print("Ok, got exception:", ex)
    else:
        raise Exception("Expected exception")
