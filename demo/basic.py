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


def main(api):
    logging.basicConfig()
    logging.getLogger("").setLevel(logging.WARNING)
    
    print("Doing stuff before flow ...")
    components = range(4)

    with serial(api, timeout=70, job_name_prefix='jenkinsflow_demo__basic__', report_interval=3) as ctrl1:
        ctrl1.invoke('prepare')

        with ctrl1.parallel(timeout=20, report_interval=3) as ctrl2:
            for component in components:
                ctrl2.invoke('deploy_component' + str(component))

        ctrl1.invoke('prepare_tests')

        with ctrl1.parallel(timeout=40, report_interval=3) as ctrl2:
            with ctrl2.serial(timeout=40, report_interval=3) as ctrl3:
                ctrl3.invoke('test_ui')
                with ctrl3.parallel(timeout=40, report_interval=3) as ctrl4:
                    for component in components:
                        ctrl4.invoke('test_server_component' + str(component))
            ctrl2.invoke('test_x')

        ctrl1.invoke('report', password='Y', s1='tst_regression', c1='complete')
        ctrl1.invoke('promote')

    print("Doing stuff after flow ...")


if __name__ == '__main__':
    main(jenkins.Jenkins(os.environ.get('JENKINS_URL') or "http://localhost:8080"))
