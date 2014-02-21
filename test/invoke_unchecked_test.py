#!/usr/bin/python

# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from jenkinsflow.flow import serial
from framework import mock_api


def test_invoke_unchecked():
    with mock_api.api(__file__) as api:
        api.flow_job()
        api.job('j1', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=None, unknown_result=True)
        api.job('j2', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=2)
        api.job('j3', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=3)
        # Make sure result is available during first invocation of _check, only way to hit error handling code in unchecked job
        api.job('j4', exec_time=0.00000000000000000000000000000000001, max_fails=1, expect_invocations=1, expect_order=None, 
                invocation_delay=0.00000000000000000000000000000000001, unknown_result=True)
        api.job('j5', exec_time=100, max_fails=0, expect_invocations=1, expect_order=None, unknown_result=True)
        api.job('j6', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=4)
        api.job('j7', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=5)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=1) as ctrl1:
            ctrl1.invoke_unchecked('j1')
            ctrl1.invoke('j2')

            with ctrl1.parallel(timeout=40, report_interval=3) as ctrl2:
                with ctrl2.serial(timeout=40, report_interval=3) as ctrl3a:
                    ctrl3a.invoke('j3')
                    ctrl3a.invoke_unchecked('j4', fail='yes')

                with ctrl2.parallel(timeout=40, report_interval=3) as ctrl3b:
                    ctrl3b.invoke_unchecked('j5')
                    ctrl3b.invoke('j6')

            ctrl1.invoke('j7')
