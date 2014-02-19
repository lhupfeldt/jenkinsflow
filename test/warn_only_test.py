#!/usr/bin/python

# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from pytest import raises

from jenkinsflow.jobcontrol import serial, parallel, FailedChildJobException, FailedChildJobsException
from framework import mock_api

from demo_security import username, password


def test_warn_only_serial():
    with mock_api.api(__file__) as api:
        api.flow_job()
        api.job('j11', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j12_fail', exec_time=0.5, max_fails=1, expect_invocations=1, expect_order=2)
        api.job('j13', exec_time=0.5, max_fails=0, expect_invocations=0, expect_order=None)

        with serial(api, timeout=70, username=username, password=password, job_name_prefix=api.job_name_prefix, report_interval=3, warn_only=True) as ctrl1:
            ctrl1.invoke('j11')
            ctrl1.invoke('j12_fail', fail='yes')
            ctrl1.invoke('j13')


def test_warn_only_parallel():
    with mock_api.api(__file__) as api:
        api.flow_job()
        api.job('j1_fail', exec_time=0.5, max_fails=1, expect_invocations=1, expect_order=1)
        api.job('j2', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=1)

        with parallel(api, timeout=70, username=username, password=password, job_name_prefix=api.job_name_prefix, report_interval=3, warn_only=True) as ctrl1:
            ctrl1.invoke('j1_fail', fail='yes')
            ctrl1.invoke('j2')


def test_warn_only_nested_serial_parallel():
    with mock_api.api(__file__) as api:
        api.flow_job()
        api.job('j11', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j21', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=2)
        api.job('j22_fail', exec_time=0.5, max_fails=1, expect_invocations=1, expect_order=2)
        api.job('j23', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=2)

        with serial(api, timeout=70, username=username, password=password, job_name_prefix=api.job_name_prefix, report_interval=3) as ctrl1:
            ctrl1.invoke('j11')

            with ctrl1.parallel(warn_only=True) as ctrl2:
                ctrl2.invoke('j21')
                ctrl2.invoke('j22_fail', fail='yes')
                ctrl2.invoke('j23')


def test_warn_only_nested_parallel_serial():
    with mock_api.api(__file__) as api:
        api.flow_job()
        api.job('j11', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j21', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j22_fail', exec_time=0.5, max_fails=1, expect_invocations=1, expect_order=1)
        api.job('j23', exec_time=0.5, max_fails=0, expect_invocations=0, expect_order=None)

        with parallel(api, timeout=70, username=username, password=password, job_name_prefix=api.job_name_prefix, report_interval=3) as ctrl1:
            ctrl1.invoke('j11')

            with ctrl1.serial(warn_only=True) as ctrl2:
                ctrl2.invoke('j21')
                ctrl2.invoke('j22_fail', fail='yes')
                ctrl2.invoke('j23')


def test_warn_only_nested_serial_serial():
    with mock_api.api(__file__) as api:
        api.flow_job()
        api.job('j11', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j21', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=2)
        api.job('j22_fail', exec_time=0.5, max_fails=1, expect_invocations=1, expect_order=2)
        api.job('j23', exec_time=0.5, max_fails=0, expect_invocations=0, expect_order=None)

        with serial(api, timeout=70, username=username, password=password, job_name_prefix=api.job_name_prefix, report_interval=3) as ctrl1:
            ctrl1.invoke('j11')

            with ctrl1.serial(warn_only=True) as ctrl2:
                ctrl2.invoke('j21')
                ctrl2.invoke('j22_fail', fail='yes')
                ctrl2.invoke('j23')


def test_warn_only_nested_parallel_parallel():
    with mock_api.api(__file__) as api:
        api.flow_job()
        api.job('j11', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j21', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j22_fail', exec_time=0.5, max_fails=1, expect_invocations=1, expect_order=1)
        api.job('j23', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=1)

        with parallel(api, timeout=70, username=username, password=password, job_name_prefix=api.job_name_prefix, report_interval=3) as ctrl1:
            ctrl1.invoke('j11')

            with ctrl1.parallel(warn_only=True) as ctrl2:
                ctrl2.invoke('j21')
                ctrl2.invoke('j22_fail', fail='yes')
                ctrl2.invoke('j23')


def test_warn_only_nested_serial_serial_continue():
    with mock_api.api(__file__) as api:
        api.flow_job()
        api.job('j11', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j21', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=2)
        api.job('j22_fail', exec_time=0.5, max_fails=1, expect_invocations=1, expect_order=3)
        api.job('j23', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=4)

        with serial(api, timeout=70, username=username, password=password, job_name_prefix=api.job_name_prefix, report_interval=3) as ctrl1:
            ctrl1.invoke('j11')

            with ctrl1.serial() as ctrl2:
                ctrl2.invoke('j21')
                with ctrl2.serial(warn_only=True) as ctrl3:
                    ctrl3.invoke('j22_fail', fail='yes')
                ctrl2.invoke('j23')


def test_warn_only_nested_parallel_serial_continue():
    with mock_api.api(__file__) as api:
        api.flow_job()
        api.job('j11', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j21', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j22_fail', exec_time=0.5, max_fails=1, expect_invocations=1, expect_order=1)
        api.job('j23', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=1)

        with parallel(api, timeout=70, username=username, password=password, job_name_prefix=api.job_name_prefix, report_interval=3) as ctrl1:
            ctrl1.invoke('j11')

            with ctrl1.serial() as ctrl2:
                ctrl2.invoke('j21')
                with ctrl2.serial(warn_only=True) as ctrl3:
                    ctrl3.invoke('j22_fail', fail='yes')
                ctrl2.invoke('j23')


def test_warn_only_nested_serial_serial_continue_fail():
    with mock_api.api(__file__) as api:
        api.flow_job()
        api.job('j11', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j21', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=2)
        api.job('j22_fail', exec_time=0.5, max_fails=1, expect_invocations=1, expect_order=3)
        api.job('j23_fail', exec_time=0.5, max_fails=1, expect_invocations=1, expect_order=4)

        with raises(FailedChildJobException):
            with serial(api, timeout=70, username=username, password=password, job_name_prefix=api.job_name_prefix, report_interval=3) as ctrl1:
                ctrl1.invoke('j11')

                with ctrl1.serial() as ctrl2:
                    ctrl2.invoke('j21')
                    with ctrl2.serial(warn_only=True) as ctrl3:
                        ctrl3.invoke('j22_fail', fail='yes')
                    ctrl2.invoke('j23_fail', fail='yes')


def test_warn_only_nested_parallel_serial_continue_fail():
    with mock_api.api(__file__) as api:
        api.flow_job()
        api.job('j11', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j21', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j22_fail', exec_time=0.5, max_fails=1, expect_invocations=1, expect_order=1)
        api.job('j23_fail', exec_time=0.5, max_fails=1, expect_invocations=1, expect_order=1)

        with raises(FailedChildJobsException):
            with parallel(api, timeout=70, username=username, password=password, job_name_prefix=api.job_name_prefix, report_interval=3) as ctrl1:
                ctrl1.invoke('j11')

                with ctrl1.serial() as ctrl2:
                    ctrl2.invoke('j21')
                    with ctrl2.serial(warn_only=True) as ctrl3:
                        ctrl3.invoke('j22_fail', fail='yes')
                    ctrl2.invoke('j23_fail', fail='yes')
