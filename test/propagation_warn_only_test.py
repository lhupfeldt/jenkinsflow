# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from pytest import raises

from jenkinsflow.flow import serial, parallel, FailedChildJobException, FailedChildJobsException, Propagation, BuildResult
from .framework import api_select
from .framework.utils import pre_existing_fake_cli


def test_propagation_warn_only_serial(api_type, fake_java):
    with api_select.api(__file__, api_type, login=True) as api:
        pre_existing_fake_cli(api_type)
        api.flow_job()
        api.job('j11', max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j12_fail', max_fails=1, expect_invocations=1, expect_order=2, serial=True)
        api.job('j13', max_fails=0, expect_invocations=0, expect_order=None)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=3, propagation=Propagation.FAILURE_TO_UNSTABLE) as ctrl1:
            ctrl1.invoke('j11')
            ctrl1.invoke('j12_fail')
            ctrl1.invoke('j13')

        assert ctrl1.result == BuildResult.UNSTABLE
        # Note: the fact that no error was raised also implies that the failure didn't propagate as failure


def test_propagation_warn_only_parallel(api_type, fake_java):
    with api_select.api(__file__, api_type, login=True) as api:
        pre_existing_fake_cli(api_type)
        api.flow_job()
        api.job('j1_fail', max_fails=1, expect_invocations=1, expect_order=1)
        api.job('j2', max_fails=0, expect_invocations=1, expect_order=1)

        with parallel(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=3, propagation=Propagation.FAILURE_TO_UNSTABLE) as ctrl1:
            ctrl1.invoke('j1_fail')
            ctrl1.invoke('j2')


def test_propagation_warn_only_nested_serial_parallel(api_type, fake_java):
    with api_select.api(__file__, api_type, login=True) as api:
        pre_existing_fake_cli(api_type)
        api.flow_job()
        api.job('j11', max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j21', max_fails=0, expect_invocations=1, expect_order=2, serial=True)
        api.job('j22_fail', max_fails=1, expect_invocations=1, expect_order=2)
        api.job('j23', max_fails=0, expect_invocations=1, expect_order=2)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=3) as ctrl1:
            ctrl1.invoke('j11')

            with ctrl1.parallel(propagation=Propagation.FAILURE_TO_UNSTABLE) as ctrl2:
                ctrl2.invoke('j21')
                ctrl2.invoke('j22_fail')
                ctrl2.invoke('j23')


def test_propagation_warn_only_nested_parallel_serial(api_type, fake_java):
    with api_select.api(__file__, api_type, login=True) as api:
        pre_existing_fake_cli(api_type)
        api.flow_job()
        api.job('j11', max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j21', max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j22_fail', max_fails=1, expect_invocations=1, expect_order=1, serial=True)
        api.job('j23', max_fails=0, expect_invocations=0, expect_order=None)

        with parallel(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=3) as ctrl1:
            ctrl1.invoke('j11')

            with ctrl1.serial(propagation=Propagation.FAILURE_TO_UNSTABLE) as ctrl2:
                ctrl2.invoke('j21')
                ctrl2.invoke('j22_fail')
                ctrl2.invoke('j23')


def test_propagation_warn_only_nested_serial_serial(api_type, fake_java):
    with api_select.api(__file__, api_type, login=True) as api:
        pre_existing_fake_cli(api_type)
        api.flow_job()
        api.job('j11', max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j21', max_fails=0, expect_invocations=1, expect_order=2)
        api.job('j22_fail', max_fails=1, expect_invocations=1, expect_order=2)
        api.job('j23', max_fails=0, expect_invocations=0, expect_order=None)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=3) as ctrl1:
            ctrl1.invoke('j11')

            with ctrl1.serial(propagation=Propagation.FAILURE_TO_UNSTABLE) as ctrl2:
                ctrl2.invoke('j21')
                ctrl2.invoke('j22_fail')
                ctrl2.invoke('j23')


def test_propagation_warn_only_nested_parallel_parallel(api_type, fake_java):
    with api_select.api(__file__, api_type, login=True) as api:
        pre_existing_fake_cli(api_type)
        api.flow_job()
        api.job('j11', max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j21', max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j22_fail', max_fails=1, expect_invocations=1, expect_order=1)
        api.job('j23', max_fails=0, expect_invocations=1, expect_order=1)

        with parallel(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=3) as ctrl1:
            ctrl1.invoke('j11')

            with ctrl1.parallel(propagation=Propagation.FAILURE_TO_UNSTABLE) as ctrl2:
                ctrl2.invoke('j21')
                ctrl2.invoke('j22_fail')
                ctrl2.invoke('j23')


def test_propagation_warn_only_nested_serial_serial_continue(api_type, fake_java):
    with api_select.api(__file__, api_type, login=True) as api:
        pre_existing_fake_cli(api_type)
        api.flow_job()
        api.job('j11', max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j21', max_fails=0, expect_invocations=1, expect_order=2)
        api.job('j22_fail', max_fails=1, expect_invocations=1, expect_order=3)
        api.job('j23', max_fails=0, expect_invocations=1, expect_order=4)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=3) as ctrl1:
            ctrl1.invoke('j11')

            with ctrl1.serial() as ctrl2:
                ctrl2.invoke('j21')
                with ctrl2.serial(propagation=Propagation.FAILURE_TO_UNSTABLE) as ctrl3:
                    ctrl3.invoke('j22_fail')
                ctrl2.invoke('j23')


def test_propagation_warn_only_nested_parallel_serial_continue(api_type, fake_java):
    with api_select.api(__file__, api_type, login=True) as api:
        pre_existing_fake_cli(api_type)
        api.flow_job()
        api.job('j11', max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j21', max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j22_fail', max_fails=1, expect_invocations=1, expect_order=1)
        api.job('j23', max_fails=0, expect_invocations=1, expect_order=1)

        with parallel(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=3) as ctrl1:
            ctrl1.invoke('j11')

            with ctrl1.serial() as ctrl2:
                ctrl2.invoke('j21')
                with ctrl2.serial(propagation=Propagation.FAILURE_TO_UNSTABLE) as ctrl3:
                    ctrl3.invoke('j22_fail')
                ctrl2.invoke('j23')


def test_propagation_warn_only_nested_serial_serial_continue_fail(api_type):
    with api_select.api(__file__, api_type, login=True) as api:
        pre_existing_fake_cli(api_type)
        api.flow_job()
        api.job('j11', max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j21', max_fails=0, expect_invocations=1, expect_order=2)
        api.job('j22_fail', max_fails=1, expect_invocations=1, expect_order=3)
        api.job('j23_fail', max_fails=1, expect_invocations=1, expect_order=4)

        with raises(FailedChildJobException):
            with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=3) as ctrl1:
                ctrl1.invoke('j11')

                with ctrl1.serial() as ctrl2:
                    ctrl2.invoke('j21')
                    with ctrl2.serial(propagation=Propagation.FAILURE_TO_UNSTABLE) as ctrl3:
                        ctrl3.invoke('j22_fail')
                    ctrl2.invoke('j23_fail')


def test_propagation_warn_only_nested_parallel_serial_continue_fail(api_type):
    with api_select.api(__file__, api_type, login=True) as api:
        pre_existing_fake_cli(api_type)
        api.flow_job()
        api.job('j11', max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j21', max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j22_fail', max_fails=1, expect_invocations=1, expect_order=1)
        api.job('j23_fail', max_fails=1, expect_invocations=1, expect_order=1)

        with raises(FailedChildJobsException):
            with parallel(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=3) as ctrl1:
                ctrl1.invoke('j11')

                with ctrl1.serial() as ctrl2:
                    ctrl2.invoke('j21')
                    with ctrl2.serial(propagation=Propagation.FAILURE_TO_UNSTABLE) as ctrl3:
                        ctrl3.invoke('j22_fail')
                    ctrl2.invoke('j23_fail')
