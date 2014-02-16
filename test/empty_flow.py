#!/usr/bin/python

# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from jenkinsflow.jobcontrol import serial, parallel
from framework import mock_api


def main():
    with mock_api.api(job_name_prefix=__file__) as api:
        api.job('job-1', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('job-2', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=2)
        api.job('job-3', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=3)
        api.job('job-4', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=4)

        with serial(api, timeout=70):
            pass

        with parallel(api, timeout=70):
            pass

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=1) as ctrl1:
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
