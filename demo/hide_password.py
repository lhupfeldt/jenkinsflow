#!/usr/bin/python

# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

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


def main():
    logging.basicConfig()
    logging.getLogger("").setLevel(logging.WARNING)
    api = jenkins.Jenkins(os.environ.get('JENKINSFLOW_JENKINSURL') or "http://localhost:8080")

    with serial(api, timeout=70, job_name_prefix='hide_password_', report_interval=3, secret_params='.*PASS.*|.*pass.*') as ctrl:
        # NOTE: In order to ensure that passwords are not displayed in a stacktrace you must never put a literal password
        # In the last line in the with statement, or in any statement that may raise an exception. You shold not really
        # put clear text paswords in you code anyway :)
        p1, p2, p3 = 'SECRET', 'sec', 'not_security'
        ctrl.invoke('passwd_args', fail='yes', password=p1, s1='no-secret', passwd=p2, PASS=p3)


if __name__ == '__main__':
    main()
