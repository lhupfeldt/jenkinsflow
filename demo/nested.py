#!/usr/bin/python

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# NOTE: To run the demo you must have the following jobs defined in jenkins/hudson
# tst_quick(password, s1, c1) # Requires parameters
# tst_wait4-1
# tst_wait5-1
# tst_wait4-2
# tst_wait10-1
# tst_wait5-2a
# tst_wait5-2b
# tst_wait5-2c

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

    with serial(api, timeout=70, report_interval=3, job_name_prefix='tst_') as ctrl1:
        ctrl1.invoke('wait4-1')

        with ctrl1.parallel(timeout=20, report_interval=3) as ctrl2:
            ctrl2.invoke('wait5-1')
            ctrl2.invoke('quick', password='Y', s1='WORLD', c1='maybe')

        ctrl1.invoke('wait4-2')

        with ctrl1.parallel(timeout=40, report_interval=3) as ctrl2:
            with ctrl2.serial(timeout=40, report_interval=3) as ctrl3:
                ctrl3.invoke('wait10-1')
                with ctrl3.parallel(timeout=40, report_interval=3) as ctrl4:
                    ctrl4.invoke('wait5-2a')
                    ctrl4.invoke('wait5-2b')

            ctrl2.invoke('quick', password='Y', s1='WORLD', c1='maybe')
            ctrl2.invoke('wait5-2c')


main()
