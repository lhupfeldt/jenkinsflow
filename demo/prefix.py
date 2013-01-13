#!/usr/bin/python

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# NOTE: To run the demo you must have the following jobs defined in jenkins/hudson
# tst2_quick1, tst2_x_quick2-1, tst2_x_quick2-2, tst2_x_quick2-3, tst2_quick3, tst2_y_z_quick4, tst2_y_quick5

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


jenkinsurl = "http://localhost:8080"

def main():
    logging.basicConfig()
    logging.getLogger("").setLevel(logging.WARNING)
    api = jenkins.Jenkins(jenkinsurl)

    with serial(api, timeout=70, report_interval=3, job_name_prefix='tst2_') as ctrl1:
        ctrl1.invoke('quick1')

        for index in 1, 2, 3:
            with ctrl1.serial(timeout=20, report_interval=3, job_name_prefix='x_') as ctrl2:
                ctrl2.invoke('quick2-' + str(index))

        ctrl1.invoke('quick3')

        with ctrl1.parallel(timeout=40, report_interval=3, job_name_prefix='y_') as ctrl2:
            with ctrl2.serial(timeout=40, report_interval=3, job_name_prefix='z_') as ctrl3:
                ctrl3.invoke('quick4')

            ctrl2.invoke('quick5')


if __name__ == '__main__':
    main()
