#!/usr/bin/python

# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import demo_setup
import os

from jenkinsapi import jenkins

from jenkinsflow.flow import serial

import demo_security as security

def main(api):
    with serial(api, timeout=70, securitytoken=security.securitytoken, job_name_prefix='jenkinsflow_demo__errors__', report_interval=3) as ctrl1:
        ctrl1.invoke('wait1-1')

        with ctrl1.parallel(timeout=40, report_interval=3) as ctrl2:
            with ctrl2.serial(timeout=40, report_interval=3) as ctrl3a:
                ctrl3a.invoke('wait2')
                ctrl3a.invoke('quick_fail-1', password='HELLO', s1='WORLD', c1='be')

                # Never invoked
                ctrl3a.invoke('quick', password='HELLO', s1='WORLD', c1='maybe')

            with ctrl2.parallel(timeout=40, report_interval=3) as ctrl3b:
                ctrl3b.invoke('wait5-2a')
                ctrl3b.invoke('quick_fail-2', password='HELLO', s1='WORLD', c1='maybe')
                ctrl3b.invoke('wait5-2b')
                ctrl3b.invoke('wait5-2c')

        # Never invoked
        ctrl1.invoke('wait1-2')


if __name__ == '__main__':
    jenkins = jenkins.Jenkins(os.environ.get('JENKINS_URL') or os.environ.get('HUDSON_URL') or "http://localhost:8080")
    main(jenkins)
