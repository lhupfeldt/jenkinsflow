#!/usr/bin/python

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import sys
import os.path
from os.path import join as jp
here = os.path.dirname(__file__)
sys.path.append(jp(here, '../..'))

import logging

from jenkinsflow.jobcontrol import serial, parallel
from jenkinsflow.unbuffered import UnBuffered

from clean_jobs_state import clean_jobs_state
import mock_api

# Unbuffered output does not work well in Jenkins, so in case
# this is run from a hudson job, we want unbuffered output
sys.stdout = UnBuffered(sys.stdout)


def main():
    clean_jobs_state()

    logging.basicConfig()
    logging.getLogger("").setLevel(logging.WARNING)    

    prefix = 'empty_flow'
    with mock_api.api(job_name_prefix=prefix) as api:
        api.mock_job('job-1', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=1)
        api.mock_job('job-2', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=2)
        api.mock_job('job-3', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=3)
        api.mock_job('job-4', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=4)

        with serial(api, timeout=70):
            pass
        
        with parallel(api, timeout=70):
            pass
        
        with serial(api, timeout=70, job_name_prefix=prefix, report_interval=1) as ctrl1:
            ctrl1.invoke('job-1')
        
            with ctrl1.parallel():
                pass
        
            with ctrl1.serial():
                pass
        
            with ctrl1.parallel() as ctrl2:
                with ctrl2.serial() as ctrl3a:
                    ctrl3a.invoke('job-2')
                    ctrl3a.invoke('job-3')
        
                with ctrl2.parallel():
                    pass
        
            ctrl1.invoke('job-4')


if __name__ == '__main__':
    main()
