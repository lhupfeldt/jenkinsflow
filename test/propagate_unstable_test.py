# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import os
from pytest import raises

from jenkinsflow.flow import parallel, serial, BuildResult, FailedChildJobException, FinalResultException

from demo_security import username, password
from .framework import api_select


def test_propagate_unstable_serial_single_unstable(api_type):
    with api_select.api(__file__, api_type, login=True) as api:
        api.flow_job()
        api.job('j11_unstable', max_fails=0, expect_invocations=1, expect_order=1, final_result='unstable')

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, raise_if_unsuccessful=False) as ctrl1:
            ctrl1.invoke('j11_unstable')

        assert ctrl1.result == BuildResult.UNSTABLE
        return 77


def test_propagate_unstable_serial_single_unstable_user_pass(api_type):
    with api_select.api(__file__, api_type) as api:
        api.flow_job()
        api.job('j11_unstable', max_fails=0, expect_invocations=1, expect_order=1, final_result='unstable')

        with serial(api, timeout=70, username=username, password=password, job_name_prefix=api.job_name_prefix, raise_if_unsuccessful=False) as ctrl1:
            ctrl1.invoke('j11_unstable')

        assert ctrl1.result == BuildResult.UNSTABLE
        return 77


def test_propagate_unstable_parallel_single_unstable(api_type):
    with api_select.api(__file__, api_type, login=True) as api:
        api.flow_job()
        api.job('j11_unstable', max_fails=0, expect_invocations=1, expect_order=1, final_result='unstable')

        with parallel(api, timeout=70, job_name_prefix=api.job_name_prefix, raise_if_unsuccessful=False) as ctrl1:
            ctrl1.invoke('j11_unstable')

        assert ctrl1.result == BuildResult.UNSTABLE
        return 77


def test_propagate_unstable_serial_toplevel(api_type):
    with api_select.api(__file__, api_type, login=True) as api:
        api.flow_job()
        api.job('j11', max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j12_unstable', max_fails=0, expect_invocations=1, expect_order=2, final_result='unstable', serial=True)
        api.job('j13', max_fails=0, expect_invocations=1, expect_order=3, serial=True)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, raise_if_unsuccessful=False) as ctrl1:
            ctrl1.invoke('j11')
            ctrl1.invoke('j12_unstable')
            ctrl1.invoke('j13')

        assert ctrl1.result == BuildResult.UNSTABLE
        return 77


def test_propagate_unstable_parallel_toplevel(api_type):
    with api_select.api(__file__, api_type, login=True) as api:
        api.flow_job()
        api.job('j11', max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j12_unstable', max_fails=0, expect_invocations=1, expect_order=1, final_result='unstable')
        api.job('j13', max_fails=0, expect_invocations=1, expect_order=1)

        with parallel(api, timeout=70, job_name_prefix=api.job_name_prefix, raise_if_unsuccessful=False) as ctrl1:
            ctrl1.invoke('j11')
            ctrl1.invoke('j12_unstable')
            ctrl1.invoke('j13')

        assert ctrl1.result == BuildResult.UNSTABLE
        return 77


def test_propagate_unstable_serial_inner(api_type):
    with api_select.api(__file__, api_type, login=True) as api:
        api.flow_job()
        api.job('j11', max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j21', max_fails=0, expect_invocations=1, expect_order=2, serial=True)
        api.job('j22_unstable', max_fails=0, expect_invocations=1, expect_order=3, final_result='unstable', serial=True)
        api.job('j23', max_fails=0, expect_invocations=1, expect_order=4, serial=True)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, raise_if_unsuccessful=False) as ctrl1:
            ctrl1.invoke('j11')
            with ctrl1.serial() as ctrl2:
                ctrl2.invoke('j21')
                ctrl2.invoke('j22_unstable')
                ctrl2.invoke('j23')

        assert ctrl2.result == BuildResult.UNSTABLE
        assert ctrl1.result == BuildResult.UNSTABLE
        return 77


def test_propagate_unstable_parallel_inner(api_type):
    with api_select.api(__file__, api_type, login=True) as api:
        api.flow_job()
        api.job('j11', max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j21', max_fails=0, expect_invocations=1, expect_order=2, serial=True)
        api.job('j22_unstable', max_fails=0, expect_invocations=1, expect_order=2, final_result='unstable')
        api.job('j23', max_fails=0, expect_invocations=1, expect_order=2)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, raise_if_unsuccessful=False) as ctrl1:
            ctrl1.invoke('j11')
            with ctrl1.parallel() as ctrl2:
                ctrl2.invoke('j21')
                ctrl2.invoke('j22_unstable')
                ctrl2.invoke('j23')

        assert ctrl2.result == BuildResult.UNSTABLE
        assert ctrl1.result == BuildResult.UNSTABLE
        return 77


def test_propagate_unstable_parallel_inner_raise_if_unsuccessful_true(api_type):
    with api_select.api(__file__, api_type, login=True) as api:
        api.flow_job()
        api.job('j11', max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j21', max_fails=0, expect_invocations=1, expect_order=2, serial=True)
        api.job('j22_unstable', max_fails=0, expect_invocations=1, expect_order=2, final_result='unstable')
        api.job('j23', max_fails=0, expect_invocations=1, expect_order=2)

        with raises(FinalResultException) as exinfo:
            with serial(api, timeout=70, job_name_prefix=api.job_name_prefix) as ctrl1:
                ctrl1.invoke('j11')
                with ctrl1.parallel() as ctrl2:
                    ctrl2.invoke('j21')
                    ctrl2.invoke('j22_unstable')
                    ctrl2.invoke('j23')

        assert exinfo.value.result == BuildResult.UNSTABLE
        assert ctrl2.result == BuildResult.UNSTABLE
        assert ctrl1.result == BuildResult.UNSTABLE
        return 77


def test_propagate_unstable_serial_inner_fail_after(api_type):
    with api_select.api(__file__, api_type, login=True) as api:
        api.flow_job()
        api.job('j11', max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j21', max_fails=0, expect_invocations=1, expect_order=2)
        api.job('j22_unstable', max_fails=0, expect_invocations=1, expect_order=3, final_result='unstable')
        api.job('j23_fail', max_fails=1, expect_invocations=1, expect_order=4)

        with raises(FailedChildJobException):
            with serial(api, timeout=70, job_name_prefix=api.job_name_prefix) as ctrl1:
                ctrl1.invoke('j11')
                with ctrl1.serial() as ctrl2:
                    ctrl2.invoke('j21')
                    ctrl2.invoke('j22_unstable')
                    ctrl2.invoke('j23_fail')


def test_propagate_unstable_parallel_inner_fail_before(api_type):
    with api_select.api(__file__, api_type, login=True) as api:
        api.flow_job()
        api.job('j11', max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j21_fail', max_fails=1, expect_invocations=1, expect_order=2, serial=True)
        api.job('j22_unstable', max_fails=0, expect_invocations=1, expect_order=2, final_result='unstable')
        api.job('j23', max_fails=0, expect_invocations=1, expect_order=2)

        with raises(FailedChildJobException):
            with serial(api, timeout=70, job_name_prefix=api.job_name_prefix) as ctrl1:
                ctrl1.invoke('j11')
                with ctrl1.parallel() as ctrl2:
                    ctrl2.invoke('j21_fail')
                    ctrl2.invoke('j22_unstable')
                    ctrl2.invoke('j23')
