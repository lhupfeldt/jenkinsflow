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
# Unbuffered output does not work well in Jenkins/Hudson, so in case
# this is run from a jenkins/hudson job, we want unbuffered output
sys.stdout = UnBuffered(sys.stdout)


def main():
    logging.basicConfig()
    logging.getLogger("").setLevel(logging.WARNING)
    api = jenkins.Jenkins(os.environ.get('JENKINSFLOW_JENKINSURL') or "http://localhost:8080")

    with serial(api, timeout=70, job_name_prefix='nested_', report_interval=3) as ctrl1:
        ctrl1.invoke('prepare')

        with ctrl1.parallel(timeout=20, report_interval=3) as ctrl2:
            ctrl2.invoke('deploy_component1')
            ctrl2.invoke('deploy_component2')

        ctrl1.invoke('report', password='Y', s1='deploy', c1='complete')
        ctrl1.invoke('prepare_tests')

        with ctrl1.parallel(timeout=40, report_interval=3) as ctrl2:
            with ctrl2.serial(timeout=40, report_interval=3) as ctrl3:
                ctrl3.invoke('test_ui')
                with ctrl3.parallel(timeout=40, report_interval=3) as ctrl4:
                    ctrl4.invoke('test_server_component1')
                    ctrl4.invoke('test_server_component2')

            ctrl2.invoke('report', password='Y', s1='tst_regression', c1='complete')
            ctrl2.invoke('promote')


if __name__ == '__main__':
    main()
