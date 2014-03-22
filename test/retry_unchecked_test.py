# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from jenkinsflow.flow import serial, parallel
from .framework import mock_api


def test_retry_unchecked_alone_serial_toplevel():
    with mock_api.api(__file__) as api:
        api.flow_job()
        api.job('j11_unchecked', 20, max_fails=1, expect_invocations=1, expect_order=1, invocation_delay=0.000000000000001, unknown_result=True)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, max_tries=2) as ctrl1:
            ctrl1.invoke_unchecked('j11_unchecked')


def test_retry_unchecked_long_running_serial_toplevel():
    with mock_api.api(__file__) as api:
        api.flow_job()
        api.job('j11_unchecked', 20, max_fails=1, expect_invocations=1, expect_order=1, unknown_result=True)
        api.job('j12_fail', 0.01, max_fails=1, expect_invocations=2, expect_order=2)
        api.job('j13', 0.01, max_fails=0, expect_invocations=1, expect_order=3, serial=True)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, max_tries=2) as ctrl1:
            ctrl1.invoke_unchecked('j11_unchecked')
            ctrl1.invoke('j12_fail')
            ctrl1.invoke('j13')


def test_retry_unchecked_long_running_parallel_toplevel():
    with mock_api.api(__file__) as api:
        api.flow_job()
        api.job('j11_unchecked', 20, max_fails=1, expect_invocations=1, expect_order=1, unknown_result=True)
        api.job('j12_fail', 0.01, max_fails=1, expect_invocations=2, expect_order=1)
        api.job('j13', 0.01, max_fails=0, expect_invocations=1, expect_order=1)

        with parallel(api, timeout=70, job_name_prefix=api.job_name_prefix, max_tries=2) as ctrl1:
            ctrl1.invoke_unchecked('j11_unchecked')
            ctrl1.invoke('j12_fail')
            ctrl1.invoke('j13')


def test_retry_unchecked_quick_serial_toplevel():
    with mock_api.api(__file__) as api:
        api.flow_job()
        api.job('j11_unchecked', 0.01, max_fails=1, expect_invocations=2, expect_order=1)
        api.job('j12_fail', 1, max_fails=1, expect_invocations=2, expect_order=2)
        api.job('j13', 0.01, max_fails=0, expect_invocations=1, expect_order=3, serial=True)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, max_tries=2) as ctrl1:
            ctrl1.invoke_unchecked('j11_unchecked')
            ctrl1.invoke('j12_fail')
            ctrl1.invoke('j13')


def test_retry_unchecked_quick_parallel_toplevel():
    with mock_api.api(__file__) as api:
        api.flow_job()
        api.job('j11_unchecked', 0.1, max_fails=1, expect_invocations=2, expect_order=1)
        api.job('j12_fail', 1, max_fails=1, expect_invocations=2, expect_order=1)
        api.job('j13', 0.01, max_fails=0, expect_invocations=1, expect_order=1)

        with parallel(api, timeout=70, job_name_prefix=api.job_name_prefix, max_tries=2) as ctrl1:
            ctrl1.invoke_unchecked('j11_unchecked')
            ctrl1.invoke('j12_fail')
            ctrl1.invoke('j13')


def test_retry_unchecked_quick_serial_outer_level():
    with mock_api.api(__file__) as api:
        api.flow_job()
        api.job('j11_unchecked', 0.01, max_fails=2, expect_invocations=3, expect_order=1)
        api.job('j12_fail', 1, max_fails=2, expect_invocations=3, expect_order=2)
        api.job('j13', 0.01, max_fails=0, expect_invocations=1, expect_order=3, serial=True)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, max_tries=2) as ctrl1:
            with ctrl1.serial(max_tries=2) as ctrl2:
                ctrl2.invoke_unchecked('j11_unchecked')
                ctrl2.invoke('j12_fail')
                ctrl2.invoke('j13')


def test_retry_unchecked_quick_parallel_outer_level():
    with mock_api.api(__file__) as api:
        api.flow_job()
        api.job('j11_unchecked', 0.1, max_fails=2, expect_invocations=3, expect_order=1)
        api.job('j12_fail', 1, max_fails=2, expect_invocations=3, expect_order=1)
        api.job('j13', 0.01, max_fails=0, expect_invocations=1, expect_order=1)

        with parallel(api, timeout=70, job_name_prefix=api.job_name_prefix, max_tries=2) as ctrl1:
            with ctrl1.parallel(max_tries=2) as ctrl2:
                ctrl2.invoke_unchecked('j11_unchecked')
                ctrl2.invoke('j12_fail')
                ctrl2.invoke('j13')
