# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from pytest import raises

from jenkinsflow.flow import parallel, serial, FlowScopeException
from .framework import api_select


def test_flow_scope_job(api_type):
    with api_select.api(__file__, api_type) as api:
        api.flow_job()
        api.job('j1', max_fails=0, expect_invocations=0, expect_order=None)
        api.job('j2', max_fails=0, expect_invocations=0, expect_order=None)

        with raises(FlowScopeException):
            with serial(api, 10, job_name_prefix=api.job_name_prefix) as ctrl1:
                pass
            ctrl1.invoke('j1')

        with raises(FlowScopeException):
            with parallel(api, 10, job_name_prefix=api.job_name_prefix) as ctrl1:
                pass
            ctrl1.invoke('j1')

        with raises(FlowScopeException):
            with serial(api, 10, job_name_prefix=api.job_name_prefix) as ctrl1:
                with ctrl1.parallel() as ctrl2:
                    pass
                ctrl2.invoke('j2')

        with raises(FlowScopeException):
            with parallel(api, 10, job_name_prefix=api.job_name_prefix) as ctrl1:
                with ctrl1.serial() as ctrl2:
                    ctrl2.invoke('j1')
                ctrl2.invoke('j2')


def test_flow_scope_serial(api_type):
    with api_select.api(__file__, api_type) as api:
        api.flow_job()

        with raises(FlowScopeException):
            with serial(api, 10, job_name_prefix=api.job_name_prefix) as ctrl1:
                pass
            with ctrl1.serial(1):
                pass

        with raises(FlowScopeException):
            with serial(api, 10, job_name_prefix=api.job_name_prefix) as ctrl1:
                pass
            with ctrl1.parallel(1):
                pass

        with raises(FlowScopeException):
            with serial(api, 10, job_name_prefix=api.job_name_prefix) as ctrl1:
                with ctrl1.serial() as ctrl2:
                    ctrl2.serial(1)
                ctrl2.serial(1)

        with raises(FlowScopeException):
            with serial(api, 10, job_name_prefix=api.job_name_prefix) as ctrl1:
                with ctrl1.serial() as ctrl2:
                    ctrl1.serial(1)


def test_flow_scope_parallel(api_type):
    with api_select.api(__file__, api_type) as api:
        api.flow_job()

        with raises(FlowScopeException):
            with parallel(api, 10, job_name_prefix=api.job_name_prefix) as ctrl1:
                pass
            with ctrl1.parallel(1):
                pass

        with raises(FlowScopeException):
            with parallel(api, 10, job_name_prefix=api.job_name_prefix) as ctrl1:
                pass
            with ctrl1.serial(1):
                pass

        with raises(FlowScopeException):
            with parallel(api, 10, job_name_prefix=api.job_name_prefix) as ctrl1:
                with ctrl1.parallel() as ctrl2:
                    ctrl2.parallel(1)
                ctrl2.parallel(1)

        with raises(FlowScopeException):
            with parallel(api, 10, job_name_prefix=api.job_name_prefix) as ctrl1:
                with ctrl1.parallel() as ctrl2:
                    ctrl1.parallel(1)
