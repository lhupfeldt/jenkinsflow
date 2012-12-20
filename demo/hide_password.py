#!/usr/bin/python

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# NOTE: To run the demo you must have the following job defined in jenkins/hudson
# passwd_args(password, s1, passwd, secret_pass, PASS) # Requires parameters


import sys
import os.path
from os.path import join as jp
here = os.path.dirname(__file__)
sys.path.append(jp(here, '../..'))

import logging

from jenkinsapi import jenkins

from jenkinsflow.jobcontrol import serial
from jenkinsflow.unbuffered import UnBuffered
sys.stdout = UnBuffered(sys.stdout)


jenkinsurl = "http://localhost:8080"

def main():
    logging.basicConfig()
    logging.getLogger("").setLevel(logging.WARNING)
    api = jenkins.Jenkins(jenkinsurl)

    with serial(api, timeout=70, report_interval=3, secret_params='.*PASS.*|.*pass.*') as ctrl:
        ctrl.invoke('passwd_args', password='SECRET', s1='no-secret', passwd='sec', PASS='not_security')
        ctrl.secret_params()

main()
