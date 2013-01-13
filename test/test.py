#!/usr/bin/python

import sys, os
from os.path import join as jp
here = os.path.abspath(os.path.dirname(__file__))

sys.path.extend([jp(here, '../..'), jp(here, '../demo')])
from jenkinsflow.jobcontrol import FlowFailException
import nested, single_level, prefix, hide_password
import single_level_errors, multi_level_errors1, multi_level_errors2

os.chdir(here)

print "Validating demos"
for demo in nested, single_level, single_level_errors, prefix:
    print ""
    demo.main()

print "Validating demos"
for demo in hide_password, multi_level_errors1, multi_level_errors2:
    print ""
    try:
        demo.main()
    except FlowFailException as ex:
        print "Ok, got exception:", ex
    else:
        raise Exception("Expected exception")
