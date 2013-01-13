#!/usr/bin/python

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# NOTE: To run the demo you must have the following jobs defined in jenkins/hudson
# tst_wait4-1
# tst_wait5-1
# tst_quick_fail

import sys
import os.path
from os.path import join as jp
here = os.path.dirname(__file__)
sys.path.append(jp(here, '../..'))

import logging

from jenkinsapi import jenkins

from jenkinsflow.jobcontrol import serial
from jenkinsflow.unbuffered import UnBuffered
# Unbuffered output does not work well in Jenkins, so in case
# this is run from a hudson job, we want unbuffered output
sys.stdout = UnBuffered(sys.stdout)


jenkinsurl = "http://localhost:8080"

def main():
    logging.basicConfig()
    logging.getLogger("").setLevel(logging.WARNING)
    api = jenkins.Jenkins(jenkinsurl)

    with serial(api, timeout=70, job_name_prefix='tst_', report_interval=3) as ctrl1:
        ctrl1.invoke('wait4-1')

        with ctrl1.parallel(timeout=20, report_interval=3) as ctrl2:
            ctrl2.invoke('wait5-1')
            ctrl2.invoke('quick_fail', password='Y', s1='WORLD', c1='maybe')

        # Never invoked because of failure in preceding 'parallel' 
        ctrl1.invoke('wait4-2')

if __name__ == '__main__':
    main()
