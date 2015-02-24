# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from pytest import raises

from jenkinsflow.flow import serial, parallel, FailedChildJobException, FailedChildJobsException, Propagation, BuildResult
from .framework import api_select


def test_propagation_warn_only_serial(env_base_url, fake_java):
    with api_select.api(__file__, login=True) as api:
        api.flow_job()
        api.job('j11', exec_time=0.01, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j12_fail', exec_time=0.01, max_fails=1, expect_invocations=1, expect_order=2, serial=True)
        api.job('j13', exec_time=0.01, max_fails=0, expect_invocations=0, expect_order=None)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=3, propagation=Propagation.FAILURE_TO_UNSTABLE) as ctrl1:
            ctrl1.invoke('j11')
            ctrl1.invoke('j12_fail')
            ctrl1.invoke('j13')

        assert ctrl1.result == BuildResult.UNSTABLE
        # Note: the fact that not error was raised also implies that the failure didn't propagat as failure


def test_propagation_warn_only_parallel(env_base_url, fake_java):
    with api_select.api(__file__, login=True) as api:
        api.flow_job()
        api.job('j1_fail', exec_time=0.01, max_fails=1, expect_invocations=1, expect_order=1)
        api.job('j2', exec_time=0.01, max_fails=0, expect_invocations=1, expect_order=1)

        with parallel(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=3, propagation=Propagation.FAILURE_TO_UNSTABLE) as ctrl1:
            ctrl1.invoke('j1_fail')
            ctrl1.invoke('j2')


def test_propagation_warn_only_nested_serial_parallel(env_base_url, fake_java):
    with api_select.api(__file__, login=True) as api:
        api.flow_job()
        api.job('j11', exec_time=0.01, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j21', exec_time=0.01, max_fails=0, expect_invocations=1, expect_order=2, serial=True)
        api.job('j22_fail', exec_time=0.01, max_fails=1, expect_invocations=1, expect_order=2)
        api.job('j23', exec_time=0.01, max_fails=0, expect_invocations=1, expect_order=2)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=3) as ctrl1:
            ctrl1.invoke('j11')

            with ctrl1.parallel(propagation=Propagation.FAILURE_TO_UNSTABLE) as ctrl2:
                ctrl2.invoke('j21')
                ctrl2.invoke('j22_fail')
                ctrl2.invoke('j23')


def test_propagation_warn_only_nested_parallel_serial(env_base_url, fake_java):
    with api_select.api(__file__, login=True) as api:
        api.flow_job()
        api.job('j11', exec_time=0.01, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j21', exec_time=0.01, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j22_fail', exec_time=0.01, max_fails=1, expect_invocations=1, expect_order=1, serial=True)
        api.job('j23', exec_time=0.01, max_fails=0, expect_invocations=0, expect_order=None)

        with parallel(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=3) as ctrl1:
            ctrl1.invoke('j11')

            with ctrl1.serial(propagation=Propagation.FAILURE_TO_UNSTABLE) as ctrl2:
                ctrl2.invoke('j21')
                ctrl2.invoke('j22_fail')
                ctrl2.invoke('j23')


def test_propagation_warn_only_nested_serial_serial(env_base_url, fake_java):
    with api_select.api(__file__, login=True) as api:
        api.flow_job()
        api.job('j11', exec_time=0.01, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j21', exec_time=0.01, max_fails=0, expect_invocations=1, expect_order=2)
        api.job('j22_fail', exec_time=0.01, max_fails=1, expect_invocations=1, expect_order=2)
        api.job('j23', exec_time=0.01, max_fails=0, expect_invocations=0, expect_order=None)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=3) as ctrl1:
            ctrl1.invoke('j11')

            with ctrl1.serial(propagation=Propagation.FAILURE_TO_UNSTABLE) as ctrl2:
                ctrl2.invoke('j21')
                ctrl2.invoke('j22_fail')
                ctrl2.invoke('j23')


def test_propagation_warn_only_nested_parallel_parallel(env_base_url, fake_java):
    with api_select.api(__file__, login=True) as api:
        api.flow_job()
        api.job('j11', exec_time=0.01, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j21', exec_time=0.01, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j22_fail', exec_time=0.01, max_fails=1, expect_invocations=1, expect_order=1)
        api.job('j23', exec_time=0.01, max_fails=0, expect_invocations=1, expect_order=1)

        with parallel(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=3) as ctrl1:
            ctrl1.invoke('j11')

            with ctrl1.parallel(propagation=Propagation.FAILURE_TO_UNSTABLE) as ctrl2:
                ctrl2.invoke('j21')
                ctrl2.invoke('j22_fail')
                ctrl2.invoke('j23')


def test_propagation_warn_only_nested_serial_serial_continue(env_base_url, fake_java):
    with api_select.api(__file__, login=True) as api:
        api.flow_job()
        api.job('j11', exec_time=0.01, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j21', exec_time=0.01, max_fails=0, expect_invocations=1, expect_order=2)
        api.job('j22_fail', exec_time=0.01, max_fails=1, expect_invocations=1, expect_order=3)
        api.job('j23', exec_time=0.01, max_fails=0, expect_invocations=1, expect_order=4)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=3) as ctrl1:
            ctrl1.invoke('j11')

            with ctrl1.serial() as ctrl2:
                ctrl2.invoke('j21')
                with ctrl2.serial(propagation=Propagation.FAILURE_TO_UNSTABLE) as ctrl3:
                    ctrl3.invoke('j22_fail')
                ctrl2.invoke('j23')


def test_propagation_warn_only_nested_parallel_serial_continue(env_base_url, fake_java):
    with api_select.api(__file__, login=True) as api:
        api.flow_job()
        api.job('j11', exec_time=0.01, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j21', exec_time=0.01, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j22_fail', exec_time=0.01, max_fails=1, expect_invocations=1, expect_order=1)
        api.job('j23', exec_time=0.01, max_fails=0, expect_invocations=1, expect_order=1)

        with parallel(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=3) as ctrl1:
            ctrl1.invoke('j11')

            with ctrl1.serial() as ctrl2:
                ctrl2.invoke('j21')
                with ctrl2.serial(propagation=Propagation.FAILURE_TO_UNSTABLE) as ctrl3:
                    ctrl3.invoke('j22_fail')
                ctrl2.invoke('j23')


def test_propagation_warn_only_nested_serial_serial_continue_fail():
    with api_select.api(__file__, login=True) as api:
        api.flow_job()
        api.job('j11', exec_time=0.01, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j21', exec_time=0.01, max_fails=0, expect_invocations=1, expect_order=2)
        api.job('j22_fail', exec_time=0.01, max_fails=1, expect_invocations=1, expect_order=3)
        api.job('j23_fail', exec_time=0.01, max_fails=1, expect_invocations=1, expect_order=4)

        with raises(FailedChildJobException):
            with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=3) as ctrl1:
                ctrl1.invoke('j11')

                with ctrl1.serial() as ctrl2:
                    ctrl2.invoke('j21')
                    with ctrl2.serial(propagation=Propagation.FAILURE_TO_UNSTABLE) as ctrl3:
                        ctrl3.invoke('j22_fail')
                    ctrl2.invoke('j23_fail')


def test_propagation_warn_only_nested_parallel_serial_continue_fail():
    with api_select.api(__file__, login=True) as api:
        api.flow_job()
        api.job('j11', exec_time=0.01, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j21', exec_time=0.01, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j22_fail', exec_time=0.01, max_fails=1, expect_invocations=1, expect_order=1)
        api.job('j23_fail', exec_time=0.01, max_fails=1, expect_invocations=1, expect_order=1)

        with raises(FailedChildJobsException):
            with parallel(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=3) as ctrl1:
                ctrl1.invoke('j11')

                with ctrl1.serial() as ctrl2:
                    ctrl2.invoke('j21')
                    with ctrl2.serial(propagation=Propagation.FAILURE_TO_UNSTABLE) as ctrl3:
                        ctrl3.invoke('j22_fail')
                    ctrl2.invoke('j23_fail')
