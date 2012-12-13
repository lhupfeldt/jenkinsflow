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

from jenkinsflow.jobcontrol import parallel, serial

jenkinsurl = "http://localhost:8080"

def main():
    logging.basicConfig()
    logging.getLogger("").setLevel(logging.INFO)

    api = jenkins.Jenkins(jenkinsurl)

    with serial(api, timeout=15, report_interval=3) as ctrl:
        ctrl.invoke('quick', password='X', s1='HELLO', c1='true')
        ctrl.invoke('wait10')
        ctrl.invoke('wait5')
    
    with parallel(api, timeout=20, report_interval=3) as ctrl:
        ctrl.invoke('quick', password='Y', s1='WORLD', c1='maybe')
        ctrl.invoke('quick_fail')
        ctrl.invoke('wait10')
        ctrl.invoke('wait10_fail')
        ctrl.invoke('wait5')
        ctrl.invoke('wait5_fail')

main()
