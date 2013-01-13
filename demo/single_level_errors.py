#!/usr/bin/python

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# NOTE: To run the demo you must have the following jobs defined in jenkins/hudson
# quick(password, s1, c1) # Requires parameters
# quick_fail
# wait10
# wait10_fail
# wait5
# wait5_fail

import sys
import os.path
from os.path import join as jp
here = os.path.dirname(__file__)
sys.path.append(jp(here, '../..'))

import logging

from jenkinsapi import jenkins

from jenkinsflow.jobcontrol import parallel, serial, FailedJobException, FailedChildJobsException, FlowTimeoutException
from jenkinsflow.unbuffered import UnBuffered
sys.stdout = UnBuffered(sys.stdout)

jenkinsurl = "http://localhost:8080"

def main():
    logging.basicConfig()
    logging.getLogger("").setLevel(logging.WARNING)
    api = jenkins.Jenkins(jenkinsurl)
    
    try:
        with parallel(api, timeout=20, report_interval=3) as ctrl:
            ctrl.invoke('quick', password='Yes', s1='', c1='false')
            ctrl.invoke('quick_fail')
            ctrl.invoke('wait10')
            ctrl.invoke('wait10_fail')
            ctrl.invoke('wait5')
            ctrl.invoke('wait5_fail')
        raise Exception("Should have failed!")
    except FailedChildJobsException as ex:
        print "Ok, got exception:", ex

    try:
        with parallel(api, timeout=1, report_interval=3) as ctrl:
            ctrl.invoke('quick', password='Yes', s1='', c1='false')
            ctrl.invoke('wait5')
        raise Exception("Should have failed!")
    except FlowTimeoutException as ex:
        print "Ok, got exception:", ex

    try:
        with serial(api, timeout=20, report_interval=3) as ctrl:
            ctrl.invoke('quick', password='Yes', s1='', c1='false')
            ctrl.invoke('quick_fail')
            ctrl.invoke('wait5')
        raise Exception("Should have failed!")
    except FailedJobException as ex:
        print "Ok, got exception:", ex

if __name__ == '__main__':
    main()
