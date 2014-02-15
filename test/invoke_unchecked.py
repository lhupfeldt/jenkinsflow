#!/usr/bin/python

# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from jenkinsflow.jobcontrol import serial
from framework import mock_api

def main():
    with mock_api.api(job_name_prefix=__file__) as api:
        api.job('job-1', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('job-2', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=2)
        api.job('job-3', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=3)
        api.job('job-4', exec_time=0.5, max_fails=-1, expect_invocations=1, expect_order=3)
        api.job('job-5', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=3)
        api.job('job-6', exec_time=0.5, max_fails=-1, expect_invocations=1, expect_order=4)
        api.job('job-7', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=5)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=1) as ctrl1:
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
