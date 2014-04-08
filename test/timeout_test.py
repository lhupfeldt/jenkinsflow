# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from pytest import raises

from jenkinsflow.flow import parallel, serial, FlowTimeoutException
from .framework import mock_api
from .framework.utils import replace_host_port


def test_timeout_top_level_serial():
    with mock_api.api(__file__) as api:
        api.job('quick', exec_time=0.01, max_fails=0, expect_invocations=1, expect_order=None, params=(('s1', '', 'desc'), ('c1', 'false', 'desc')))
        api.job('wait20', exec_time=20, max_fails=0, expect_invocations=1, expect_order=None, unknown_result=True, serial=True)

        with raises(FlowTimeoutException):
            with serial(api, timeout=8, job_name_prefix=api.job_name_prefix, report_interval=3) as ctrl:
                ctrl.invoke('quick', s1='', c1=False)
                ctrl.invoke('wait20')


def test_timeout_top_level_parallel():
    with mock_api.api(__file__) as api:
        api.job('quick', exec_time=0.01, max_fails=0, expect_invocations=1, expect_order=None, params=(('s1', '', 'desc'), ('c1', 'false', 'desc')))
        api.job('wait20', exec_time=20, max_fails=0, expect_invocations=1, expect_order=None, unknown_result=True)

        with raises(FlowTimeoutException):
            with parallel(api, timeout=8, job_name_prefix=api.job_name_prefix, report_interval=3) as ctrl:
                ctrl.invoke('quick', s1='', c1=False)
                ctrl.invoke('wait20')


def test_timeout_inner_level_serial():
    with mock_api.api(__file__) as api:
        api.job('quick11', exec_time=0.01, max_fails=0, expect_invocations=1, expect_order=None)
        api.job('quick21', exec_time=0.01, max_fails=0, expect_invocations=1, expect_order=None)
        api.job('wait20', exec_time=20, max_fails=0, expect_invocations=1, expect_order=None, unknown_result=True, serial=True)

        with raises(FlowTimeoutException) as exinfo:
            with parallel(api, timeout=3000, job_name_prefix=api.job_name_prefix, report_interval=3) as ctrl1:
                ctrl1.invoke('quick11')
                with ctrl1.serial(timeout=8) as ctrl2:
                    ctrl2.invoke('quick21')
                    ctrl2.invoke('wait20')

        assert "Timeout after:" in exinfo.value.message
        assert ", in flow ['jenkinsflow_test__timeout_inner_level_serial__quick21', 'jenkinsflow_test__timeout_inner_level_serial__wait20']. Unfinished jobs:['http://x.x/job/jenkinsflow_test__timeout_inner_level_serial__wait20 - /build']" in replace_host_port(exinfo.value.message)



def test_timeout_inner_level_parallel():
    with mock_api.api(__file__) as api:
        api.job('quick11', exec_time=0.01, max_fails=0, expect_invocations=1, expect_order=None)
        api.job('quick21', exec_time=0.01, max_fails=0, expect_invocations=1, expect_order=None)
        api.job('wait20', exec_time=30, max_fails=0, expect_invocations=1, expect_order=None, unknown_result=True)

        with raises(FlowTimeoutException) as exinfo:
            with serial(api, timeout=3000, job_name_prefix=api.job_name_prefix, report_interval=3) as ctrl1:
                ctrl1.invoke('quick11')
                with ctrl1.parallel(timeout=8) as ctrl2:
                    ctrl2.invoke('quick21')
                    ctrl2.invoke('wait20')

        assert "Timeout after:" in exinfo.value.message
        assert ", in flow ('jenkinsflow_test__timeout_inner_level_parallel__quick21', 'jenkinsflow_test__timeout_inner_level_parallel__wait20'). Unfinished jobs:['http://x.x/job/jenkinsflow_test__timeout_inner_level_parallel__wait20 - /build']" in replace_host_port(exinfo.value.message)


def test_timeout_multi_level_mix():
    with mock_api.api(__file__) as api:
        api.job('quick11', exec_time=0.01, max_fails=0, expect_invocations=1, expect_order=None)
        api.job('quick21', exec_time=0.01, max_fails=0, expect_invocations=1, expect_order=None)
        api.job('wait20_22', exec_time=30, max_fails=0, expect_invocations=1, expect_order=None, unknown_result=True)
        api.job('wait20_31', exec_time=30, max_fails=0, expect_invocations=1, expect_order=None, unknown_result=True)

        with raises(FlowTimeoutException) as exinfo:
            with serial(api, timeout=3000, job_name_prefix=api.job_name_prefix, report_interval=3) as ctrl1:
                ctrl1.invoke('quick11')
                with ctrl1.parallel(timeout=8) as ctrl2:
                    ctrl2.invoke('quick21')
                    ctrl2.invoke('wait20_22')
                    with ctrl2.parallel() as ctrl3:
                        ctrl3.invoke('wait20_31')

        assert "Timeout after:" in exinfo.value.message
        assert ", in flow ('jenkinsflow_test__timeout_multi_level_mix__quick21', 'jenkinsflow_test__timeout_multi_level_mix__wait20_22', ('jenkinsflow_test__timeout_multi_level_mix__wait20_31',)). Unfinished jobs:['http://x.x/job/jenkinsflow_test__timeout_multi_level_mix__wait20_22 - /build', \"('jenkinsflow_test__timeout_multi_level_mix__wait20_31',)\"]" in replace_host_port(exinfo.value.message)
