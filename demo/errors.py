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
# Unbuffered output does not work well in Jenkins, so in case
# this is run from a hudson job, we want unbuffered output
sys.stdout = UnBuffered(sys.stdout)


def main():
    logging.basicConfig()
    logging.getLogger("").setLevel(logging.WARNING)
    api = jenkins.Jenkins(os.environ.get('JENKINSFLOW_JENKINSURL') or "http://localhost:8080")

    with serial(api, timeout=70, job_name_prefix='errors_', report_interval=3) as ctrl1:
        ctrl1.invoke('wait1-1')

        with ctrl1.parallel(timeout=40, report_interval=3) as ctrl2:
            with ctrl2.serial(timeout=40, report_interval=3) as ctrl3a:
                ctrl3a.invoke('wait2')
                ctrl3a.invoke('quick_fail-1', password='HELLO', fail='yes', s1='WORLD', c1='be')

                # Never invoked
                ctrl3a.invoke('quick', password='HELLO', s1='WORLD', c1='maybe')

            with ctrl2.parallel(timeout=40, report_interval=3) as ctrl3b:
                ctrl3b.invoke('wait5-2a')
                ctrl3b.invoke('quick_fail-2', password='HELLO', fail='yes', s1='WORLD', c1='maybe')
                ctrl3b.invoke('wait5-2b')
                ctrl3b.invoke('wait5-2c')

        # Never invoked
        ctrl1.invoke('wait1-2')


if __name__ == '__main__':
    main()
