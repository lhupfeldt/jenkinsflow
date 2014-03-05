#!/usr/bin/python

# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from pytest import raises

from jenkinsflow.flow import parallel, serial, FlowTimeoutException
from framework import mock_api


def test_timeout_top_level_serial():
    with mock_api.api(__file__) as api:
        api.job('quick', exec_time=0.01, max_fails=0, expect_invocations=1, expect_order=None, params=(('s1', '', 'desc'), ('c1', 'false', 'desc')))
        api.job('wait10', exec_time=10, max_fails=0, expect_invocations=1, expect_order=None, unknown_result=True)

        with raises(FlowTimeoutException):
            with serial(api, timeout=8, job_name_prefix=api.job_name_prefix, report_interval=3) as ctrl:
                ctrl.invoke('quick', s1='', c1=False)
                ctrl.invoke('wait10')


def test_timeout_top_level_parallel():
    with mock_api.api(__file__) as api:
        api.job('quick', exec_time=0.01, max_fails=0, expect_invocations=1, expect_order=None, params=(('s1', '', 'desc'), ('c1', 'false', 'desc')))
        api.job('wait10', exec_time=10, max_fails=0, expect_invocations=1, expect_order=None, unknown_result=True)

        with raises(FlowTimeoutException):
            with parallel(api, timeout=8, job_name_prefix=api.job_name_prefix, report_interval=3) as ctrl:
                ctrl.invoke('quick', s1='', c1=False)
                ctrl.invoke('wait10')


def test_timeout_inner_level_serial():
    with mock_api.api(__file__) as api:
        api.job('quick11', exec_time=0.01, max_fails=0, expect_invocations=1, expect_order=None)
        api.job('quick21', exec_time=0.01, max_fails=0, expect_invocations=1, expect_order=None)
        api.job('wait10', exec_time=10, max_fails=0, expect_invocations=1, expect_order=None, unknown_result=True)

        with raises(FlowTimeoutException) as exinfo:
            with parallel(api, timeout=3000, job_name_prefix=api.job_name_prefix, report_interval=3) as ctrl1:
                ctrl1.invoke('quick11', s1='', c1=False)
                with ctrl1.serial(timeout=8) as ctrl2:
                    ctrl2.invoke('quick21')
                    ctrl2.invoke('wait10')

        assert "Timeout after" in exinfo.value.message


def test_timeout_inner_level_parallel():
    with mock_api.api(__file__) as api:
        api.job('quick11', exec_time=0.01, max_fails=0, expect_invocations=1, expect_order=None)
        api.job('quick21', exec_time=0.01, max_fails=0, expect_invocations=1, expect_order=None)
        api.job('wait10', exec_time=10, max_fails=0, expect_invocations=1, expect_order=None, unknown_result=True)

        with raises(FlowTimeoutException) as exinfo:
            with serial(api, timeout=3000, job_name_prefix=api.job_name_prefix, report_interval=3) as ctrl1:
                ctrl1.invoke('quick11', s1='', c1=False)
                with ctrl1.parallel(timeout=8) as ctrl2:
                    ctrl2.invoke('quick21')
                    ctrl2.invoke('wait10')

        assert "Timeout after" in exinfo.value.message
