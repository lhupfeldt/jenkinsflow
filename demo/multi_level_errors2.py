#!/usr/bin/python

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# NOTE: To run the demo you must have the following jobs defined in jenkins/hudson
# tst_quick(password, s1, c1) # Requires parameters
# tst_wait2
# tst_wait4-1
# tst_wait5-2a
# tst_wait5-2b
# tst_wait5-2c
# tst_quick_fail-1(password, s1, c1) # Requires parameters
# tst_quick_fail-2(password, s1, c1) # Requires parameters

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

        with ctrl1.parallel(timeout=40, report_interval=3) as ctrl2:
            with ctrl2.serial(timeout=40, report_interval=3) as ctrl3a:
                ctrl3a.invoke('wait2')
                ctrl3a.invoke('quick_fail-1', password='HELLO', s1='WORLD', c1='maybe')

                # Never invoked
                ctrl3a.invoke('quick', password='HELLO', s1='WORLD', c1='maybe')

            with ctrl2.parallel(timeout=40, report_interval=3) as ctrl3b:
                ctrl3b.invoke('wait5-2a')
                ctrl3b.invoke('wait5-2b')
                ctrl3b.invoke('wait5-2c')
                ctrl3b.invoke('quick_fail-2', password='HELLO', s1='WORLD', c1='maybe')


if __name__ == '__main__':
    main()
