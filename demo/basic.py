#!/usr/bin/env python3

# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# Just a simple flow

from jenkinsflow.flow import serial

import lib.get_jenkins_api


def main(api, securitytoken):
    demo_name = 'jenkinsflow_demo__basic'

    with serial(api, timeout=70, securitytoken=securitytoken, job_name_prefix=demo_name + '__', report_interval=3) as outer_ctrl:
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
    main(*lib.get_jenkins_api.get_jenkins_api())
