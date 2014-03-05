# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from pytest import raises

from jenkinsflow.flow import parallel, serial, FlowScopeException
from framework import mock_api


def test_flow_scope_job():
    with mock_api.api(__file__) as api:
        api.flow_job()
        api.job('j1', 0.01, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j2', 0.01, max_fails=0, expect_invocations=0, expect_order=None)

        with raises(FlowScopeException):
            with serial(api, 5, job_name_prefix=api.job_name_prefix) as ctrl1:
                pass
            ctrl1.invoke('j1')

        with raises(FlowScopeException):
            with parallel(api, 5, job_name_prefix=api.job_name_prefix) as ctrl1:
                pass
            ctrl1.invoke('j1')

        with raises(FlowScopeException):
            with serial(api, 5, job_name_prefix=api.job_name_prefix) as ctrl1:
                with ctrl1.parallel() as ctrl2:
                    pass
                ctrl2.invoke('j2')

        with raises(FlowScopeException):
            with parallel(api, 5, job_name_prefix=api.job_name_prefix) as ctrl1:
                with ctrl1.serial() as ctrl2:
                    ctrl2.invoke('j1')
                ctrl2.invoke('j2')


def test_flow_scope_serial():
    with mock_api.api(__file__) as api:
        api.flow_job()

        with raises(FlowScopeException):
            with serial(api, 5, job_name_prefix=api.job_name_prefix) as ctrl1:
                pass
            with ctrl1.serial(1):
                pass

        with raises(FlowScopeException):
            with serial(api, 5, job_name_prefix=api.job_name_prefix) as ctrl1:
                pass
            with ctrl1.parallel(1):
                pass

        with raises(FlowScopeException):
            with serial(api, 5, job_name_prefix=api.job_name_prefix) as ctrl1:
                with ctrl1.serial() as ctrl2:
                    ctrl2.serial(1)
                ctrl2.serial(1)

        with raises(FlowScopeException):
            with serial(api, 5, job_name_prefix=api.job_name_prefix) as ctrl1:
                with ctrl1.serial() as ctrl2:
                    ctrl1.serial(1)


def test_flow_scope_parallel():
    with mock_api.api(__file__) as api:
        api.flow_job()

        with raises(FlowScopeException):
            with parallel(api, 5, job_name_prefix=api.job_name_prefix) as ctrl1:
                pass
            with ctrl1.parallel(1):
                pass

        with raises(FlowScopeException):
            with parallel(api, 5, job_name_prefix=api.job_name_prefix) as ctrl1:
                pass
            with ctrl1.serial(1):
                pass

        with raises(FlowScopeException):
            with parallel(api, 5, job_name_prefix=api.job_name_prefix) as ctrl1:
                with ctrl1.parallel() as ctrl2:
                    ctrl2.parallel(1)
                ctrl2.parallel(1)

        with raises(FlowScopeException):
            with parallel(api, 5, job_name_prefix=api.job_name_prefix) as ctrl1:
                with ctrl1.parallel() as ctrl2:
                    ctrl1.parallel(1)
