#!/usr/bin/python

# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import sys
import os.path
from os.path import join as jp
here = os.path.dirname(__file__)
sys.path.append(jp(here, '../..'))

import logging

from jenkinsflow.jobcontrol import serial
from jenkinsflow.unbuffered import UnBuffered

from framework import mock_api

# Unbuffered output does not work well in Jenkins, so in case
# this is run from a hudson job, we want unbuffered output
sys.stdout = UnBuffered(sys.stdout)

def main():
    logging.basicConfig()
    logging.getLogger("").setLevel(logging.WARNING)    

    with mock_api.api(job_name_prefix='iu_') as api:
        api.mock_job('job-1', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=1)
        api.mock_job('job-2', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=2)
        api.mock_job('job-3', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=3)
        api.mock_job('job-4', exec_time=0.5, max_fails=-1, expect_invocations=1, expect_order=3)
        api.mock_job('job-5', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=3)
        api.mock_job('job-6', exec_time=0.5, max_fails=-1, expect_invocations=1, expect_order=4)
        api.mock_job('job-7', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=5)

        with serial(api, timeout=70, job_name_prefix='iu_', report_interval=1) as ctrl1:
            ctrl1.invoke('job-1')
            ctrl1.invoke('job-2')
    
            with ctrl1.parallel(timeout=40, report_interval=3) as ctrl2:
                with ctrl2.serial(timeout=40, report_interval=3) as ctrl3a:
                    ctrl3a.invoke('job-3')
                    ctrl3a.invoke_unchecked('job-6')
    
                with ctrl2.parallel(timeout=40, report_interval=3) as ctrl3b:
                    ctrl3b.invoke_unchecked('job-4')
                    ctrl3b.invoke('job-5')
    
            ctrl1.invoke('job-7')

if __name__ == '__main__':
    main()
