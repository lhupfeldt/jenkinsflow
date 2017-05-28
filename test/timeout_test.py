# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from pytest import raises

from jenkinsflow.flow import parallel, serial, FlowTimeoutException
from .framework import api_select


def test_timeout_top_level_serial(api_type):
    with api_select.api(__file__, api_type, login=True) as api:
        api.job('quick', max_fails=0, expect_invocations=1, expect_order=None, params=(('s1', '', 'desc'), ('c1', 'false', 'desc')))
        api.job('wait20', max_fails=0, expect_invocations=1, expect_order=None, exec_time=20, unknown_result=True, serial=True)

        with raises(FlowTimeoutException):
            with serial(api, timeout=8, job_name_prefix=api.job_name_prefix, report_interval=3) as ctrl:
                ctrl.invoke('quick', s1='', c1=False)
                ctrl.invoke('wait20')


def test_timeout_top_level_parallel(api_type):
    with api_select.api(__file__, api_type, login=True) as api:
        api.job('quick', max_fails=0, expect_invocations=1, expect_order=None, params=(('s1', '', 'desc'), ('c1', 'false', 'desc')))
        api.job('wait20', max_fails=0, expect_invocations=1, expect_order=None, exec_time=20, unknown_result=True)

        with raises(FlowTimeoutException):
            with parallel(api, timeout=8, job_name_prefix=api.job_name_prefix, report_interval=3) as ctrl:
                ctrl.invoke('quick', s1='', c1=False)
                ctrl.invoke('wait20')


def test_timeout_inner_level_serial(api_type):
    with api_select.api(__file__, api_type, login=True) as api:
        api.job('quick11', max_fails=0, expect_invocations=1, expect_order=None)
        api.job('quick21', max_fails=0, expect_invocations=1, expect_order=None)
        api.job('wait20', max_fails=0, expect_invocations=1, expect_order=None, exec_time=20, unknown_result=True, serial=True)

        with raises(FlowTimeoutException) as exinfo:
            with parallel(api, timeout=3000, job_name_prefix=api.job_name_prefix, report_interval=3) as ctrl1:
                ctrl1.invoke('quick11')
                with ctrl1.serial(timeout=8) as ctrl2:
                    ctrl2.invoke('quick21')
                    ctrl2.invoke('wait20')

        assert "Timeout after:" in str(exinfo.value)
        assert ", in flow ['jenkinsflow_test__timeout_inner_level_serial__quick21', 'jenkinsflow_test__timeout_inner_level_serial__wait20']. Unfinished jobs:['jenkinsflow_test__timeout_inner_level_serial__wait20']" in str(exinfo.value)



def test_timeout_inner_level_parallel(api_type):
    with api_select.api(__file__, api_type, login=True) as api:
        api.job('quick11', max_fails=0, expect_invocations=1, expect_order=None)
        api.job('quick21', max_fails=0, expect_invocations=1, expect_order=None)
        api.job('wait20', max_fails=0, expect_invocations=1, expect_order=None, exec_time=30, unknown_result=True)

        with raises(FlowTimeoutException) as exinfo:
            with serial(api, timeout=3000, job_name_prefix=api.job_name_prefix, report_interval=3) as ctrl1:
                ctrl1.invoke('quick11')
                with ctrl1.parallel(timeout=8) as ctrl2:
                    ctrl2.invoke('quick21')
                    ctrl2.invoke('wait20')

        assert "Timeout after:" in str(exinfo.value)
        assert ", in flow ('jenkinsflow_test__timeout_inner_level_parallel__quick21', 'jenkinsflow_test__timeout_inner_level_parallel__wait20'). Unfinished jobs:['jenkinsflow_test__timeout_inner_level_parallel__wait20']" in str(exinfo.value)


def test_timeout_multi_level_mix(api_type):
    with api_select.api(__file__, api_type, login=True) as api:
        api.job('quick11', max_fails=0, expect_invocations=1, expect_order=None)
        api.job('quick21', max_fails=0, expect_invocations=1, expect_order=None)
        api.job('wait20_22', max_fails=0, expect_invocations=1, expect_order=None, exec_time=30, unknown_result=True)
        api.job('wait20_31', max_fails=0, expect_invocations=1, expect_order=None, exec_time=30, unknown_result=True)

        with raises(FlowTimeoutException) as exinfo:
            with serial(api, timeout=3000, job_name_prefix=api.job_name_prefix, report_interval=3) as ctrl1:
                ctrl1.invoke('quick11')
                with ctrl1.parallel(timeout=8) as ctrl2:
                    ctrl2.invoke('quick21')
                    ctrl2.invoke('wait20_22')
                    with ctrl2.parallel() as ctrl3:
                        ctrl3.invoke('wait20_31')

        assert "Timeout after:" in str(exinfo.value)
        assert ", in flow ('jenkinsflow_test__timeout_multi_level_mix__quick21', 'jenkinsflow_test__timeout_multi_level_mix__wait20_22', ('jenkinsflow_test__timeout_multi_level_mix__wait20_31',)). Unfinished jobs:['jenkinsflow_test__timeout_multi_level_mix__wait20_22', ('jenkinsflow_test__timeout_multi_level_mix__wait20_31',)]" in str(exinfo.value)
