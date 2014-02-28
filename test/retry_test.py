#!/usr/bin/python

# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from jenkinsflow.flow import parallel, serial
from framework import mock_api


def test_retry_serial_toplevel():
    with mock_api.api(__file__) as api:
        api.flow_job()
        api.job('j11', 0.1, max_fails=0, expect_invocations=2, expect_order=1)
        api.job('j12_fail', 0.1, max_fails=1, expect_invocations=2, expect_order=2)
        api.job('j13', 0.1, max_fails=0, expect_invocations=1, expect_order=3)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, max_tries=2) as ctrl1:
            ctrl1.invoke('j11')
            ctrl1.invoke('j12_fail')
            ctrl1.invoke('j13')


def test_retry_parallel_toplevel():
    with mock_api.api(__file__) as api:
        api.flow_job()
        api.job('j11', 0.1, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j12_fail', 0.1, max_fails=1, expect_invocations=2, expect_order=1)
        api.job('j13', 0.1, max_fails=0, expect_invocations=1, expect_order=1)

        with parallel(api, timeout=70, job_name_prefix=api.job_name_prefix, max_tries=2) as ctrl1:
            ctrl1.invoke('j11')
            ctrl1.invoke('j12_fail')
            ctrl1.invoke('j13')


def test_retry_serial_inner():
    with mock_api.api(__file__) as api:
        api.flow_job()
        api.job('j11', 0.1, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j21', 0.1, max_fails=0, expect_invocations=2, expect_order=2)
        api.job('j22_fail', 0.1, max_fails=1, expect_invocations=2, expect_order=3)
        api.job('j23', 0.1, max_fails=0, expect_invocations=1, expect_order=4)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix) as ctrl1:
            ctrl1.invoke('j11')
            with ctrl1.serial(max_tries=2) as ctrl2:
                ctrl2.invoke('j21')
                ctrl2.invoke('j22_fail')
                ctrl2.invoke('j23')


def test_retry_parallel_inner():
    with mock_api.api(__file__) as api:
        api.flow_job()
        api.job('j11', 0.1, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j21', 0.1, max_fails=0, expect_invocations=1, expect_order=2)
        api.job('j22_fail', 0.1, max_fails=1, expect_invocations=2, expect_order=2)
        api.job('j23', 0.1, max_fails=0, expect_invocations=1, expect_order=2)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix) as ctrl1:
            ctrl1.invoke('j11')
            with ctrl1.parallel(max_tries=2) as ctrl2:
                ctrl2.invoke('j21')
                ctrl2.invoke('j22_fail')
                ctrl2.invoke('j23')


def test_retry_serial_through_parent_serial_level():
    with mock_api.api(__file__) as api:
        api.flow_job()
        api.job('j11', 0.1, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j21', 0.1, max_fails=0, expect_invocations=2, expect_order=2)
        api.job('j31_fail', 0.1, max_fails=2, expect_invocations=3, expect_order=3)
        api.job('j32', 0.1, max_fails=0, expect_invocations=1, expect_order=4)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix) as ctrl1:
            ctrl1.invoke('j11')
            with ctrl1.serial(timeout=70, max_tries=2) as ctrl2:
                ctrl2.invoke('j21')
                with ctrl2.serial(timeout=70, max_tries=2) as ctrl3:
                    ctrl3.invoke('j31_fail')
                    ctrl3.invoke('j32')


def test_retry_serial_through_parent_parallel_level():
    with mock_api.api(__file__) as api:
        api.flow_job()
        api.job('j11', 0.1, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j21', 0.1, max_fails=0, expect_invocations=1, expect_order=2)
        api.job('j31_fail', 0.1, max_fails=2, expect_invocations=3, expect_order=2)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix) as ctrl1:
            ctrl1.invoke('j11')
            with ctrl1.parallel(timeout=70, max_tries=2) as ctrl2:
                ctrl2.invoke('j21')
                with ctrl2.serial(timeout=70, max_tries=2) as ctrl3:
                    ctrl3.invoke('j31_fail')


def test_retry_parallel_through_parent_serial_level():
    with mock_api.api(__file__) as api:
        api.flow_job()
        api.job('j11', 0.1, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j21', 0.1, max_fails=0, expect_invocations=2, expect_order=2)
        api.job('j31_fail', 0.1, max_fails=2, expect_invocations=3, expect_order=3)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix) as ctrl1:
            ctrl1.invoke('j11')
            with ctrl1.serial(timeout=70, max_tries=2) as ctrl2:
                ctrl2.invoke('j21')
                with ctrl2.parallel(timeout=70, max_tries=2) as ctrl3:
                    ctrl3.invoke('j31_fail')


def test_retry_parallel_through_parent_parallel_level():
    with mock_api.api(__file__) as api:
        api.flow_job()
        api.job('j11', 0.1, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j21', 0.1, max_fails=0, expect_invocations=1, expect_order=2)
        api.job('j22_fail', 0.1, max_fails=1, expect_invocations=2, expect_order=2)
        api.job('j31_fail', 0.1, max_fails=2, expect_invocations=3, expect_order=2)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix) as ctrl1:
            ctrl1.invoke('j11')
            with ctrl1.parallel(timeout=70, max_tries=2) as ctrl2:
                ctrl2.invoke('j21')
                ctrl2.invoke('j22_fail')
                with ctrl2.parallel(timeout=70, max_tries=2) as ctrl3:
                    ctrl3.invoke('j31_fail')


def test_retry_parallel_through_outer_level():
    with mock_api.api(__file__) as api:
        api.flow_job()
        api.job('j11', 0.1, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j21', 0.1, max_fails=0, expect_invocations=1, expect_order=2)
        api.job('j31', 0.1, max_fails=0, expect_invocations=1, expect_order=3)
        api.job('j41_fail', 0.1, max_fails=2, expect_invocations=3, expect_order=3)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix) as ctrl1:
            ctrl1.invoke('j11')
            with ctrl1.serial(timeout=70, max_tries=2) as ctrl2:
                ctrl2.invoke('j21')
                with ctrl2.parallel(timeout=70) as ctrl3:
                    ctrl3.invoke('j31')
                    with ctrl3.parallel(timeout=70, max_tries=2) as ctrl4:
                        ctrl4.invoke('j41_fail')


def test_retry_serial_through_outer_level():
    with mock_api.api(__file__) as api:
        api.flow_job()
        api.job('j11', 0.1, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j21', 0.1, max_fails=0, expect_invocations=1, expect_order=2)
        api.job('j31', 0.1, max_fails=0, expect_invocations=1, expect_order=3)
        api.job('j41', 0.1, max_fails=0, expect_invocations=4, expect_order=3)
        api.job('j42_fail', 0.1, max_fails=3, expect_invocations=4, expect_order=3)
        api.job('j43', 0.1, max_fails=0, expect_invocations=1, expect_order=3)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, max_tries=2) as ctrl1:
            ctrl1.invoke('j11')
            with ctrl1.serial(timeout=70) as ctrl2:
                ctrl2.invoke('j21')
                with ctrl2.parallel(timeout=70) as ctrl3:
                    ctrl3.invoke('j31')
                    with ctrl3.serial(timeout=70, max_tries=2) as ctrl4:
                        ctrl4.invoke('j41')
                        ctrl4.invoke('j42_fail')
                        ctrl4.invoke('j43')


def test_retry_mix():
    with mock_api.api(__file__) as api:
        api.flow_job()
        api.job('j11_fail', 0.1, max_fails=1, expect_invocations=2, expect_order=1)
        api.job('j12', 0.1, max_fails=0, expect_invocations=1, expect_order=2)
        api.job('j21', 0.1, max_fails=0, expect_invocations=1, expect_order=3)
        api.job('j22_fail', 0.1, max_fails=2, expect_invocations=3, expect_order=3)
        api.job('j31_fail', 0.1, max_fails=3, expect_invocations=4, expect_order=3)
        api.job('j32', 0.1, max_fails=0, expect_invocations=1, expect_order=3)
        api.job('j23', 0.1, max_fails=0, expect_invocations=1, expect_order=3)
        api.job('j13', 0.1, max_fails=0, expect_invocations=1, expect_order=4)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, max_tries=2) as ctrl1:
            ctrl1.invoke('j11_fail')
            ctrl1.invoke('j12')

            with ctrl1.parallel(timeout=70, max_tries=3) as ctrl2:
                ctrl2.invoke('j21')
                ctrl2.invoke('j22_fail')
                with ctrl2.serial(timeout=70, max_tries=2) as ctrl3:
                    ctrl3.invoke('j31_fail')
                    ctrl3.invoke('j32')
                ctrl2.invoke('j23')

            ctrl1.invoke('j13')
