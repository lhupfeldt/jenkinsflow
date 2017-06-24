#!/usr/bin/env python

# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# Just a simple flow

from __future__ import print_function
import demo_setup
demo_setup.sys_path()

from jenkinsflow.flow import serial
import demo_security as security


def main(api):
    demo_name = 'jenkinsflow_demo__basic'

    with serial(api, timeout=70, securitytoken=security.securitytoken, job_name_prefix=demo_name + '__', report_interval=3) as outer_ctrl:
        outer_ctrl.invoke('prepare')
        outer_ctrl.invoke('deploy_component')

        with outer_ctrl.parallel(timeout=0, report_interval=3) as report_prepare_ctrl:
            report_prepare_ctrl.invoke('report_deploy')
            report_prepare_ctrl.invoke('prepare_tests')

        with outer_ctrl.parallel(timeout=0, report_interval=3) as test_ctrl:
            test_ctrl.invoke('test_x')
            test_ctrl.invoke('test_y')

        outer_ctrl.invoke('report', password='Y', s1='tst', c1='complete')


if __name__ == '__main__':
    import os
    from jenkinsflow.jenkins_api import Jenkins
    url = os.environ.get('JENKINS_URL') or os.environ.get('HUDSON_URL') or "http://localhost:8080"
    main(Jenkins(url, username=security.username, password=security.password) if security.default_use_login else Jenkins(url))
