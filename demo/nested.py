#!/usr/bin/python

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

from unbuffered import UnBuffered
sys.stdout = UnBuffered(sys.stdout)

from jenkinsflow.jobcontrol import serial, _Serial

jenkinsurl = "http://localhost:8080"

def main():
    logging.basicConfig()
    logging.getLogger("").setLevel(logging.WARNING)
    api = jenkins.Jenkins(jenkinsurl)

    with serial(api, timeout=70, report_interval=3) as ctrl1:
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
