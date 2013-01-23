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
        # NOTE: In order to ensure that passwords are not displayed in a stacktrace you must never put a literal password 
        # In the last line in the with statement, or in any statement that may raise an exception. You shold not really
        # put clean text paswords in you code anyway :)
        p1, p2, p3 = 'SECRET', 'sec', 'not_security'
        ctrl.invoke('passwd_args', password=p1, s1='no-secret', passwd=p2, PASS=p3)


if __name__ == '__main__':
    main()
