#!/usr/bin/python

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# NOTE: To run the demo you must have the following jobs defined in jenkins/hudson
# tst_quick(password, s1, c1) # Requires parameters
# tst_wait2
# tst_wait4-1
# tst_wait5-2a
# tst_wait5-2b
# tst_wait5-2c
# tst_quick_fail_n_times-1(MAX_FAILS=2) # Requires parameters
# tst_quick_fail_n_times-2(MAX_FAILS=3) # Requires parameters

import sys
import os.path
from os.path import join as jp
here = os.path.dirname(__file__)
sys.path.append(jp(here, '../..'))

import logging

from jenkinsflow.jobcontrol import serial
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

    api = mock_api.api(job_name_prefix='iu_')
    if mock_api.is_mocked:
        with api:
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

    if mock_api.is_mocked:
        api.test_results()

if __name__ == '__main__':
    main()
