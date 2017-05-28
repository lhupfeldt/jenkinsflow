# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from jenkinsflow.flow import serial, parallel
from .framework import api_select


def test_invoke_unchecked_dont_wait_serial(api_type):
    with api_select.api(__file__, api_type, login=True) as api:
        api.flow_job()
        api.job('j11_slow_unchecked', max_fails=0, expect_invocations=1, expect_order=1, exec_time=100, unknown_result=True)
        api.job('j12', max_fails=0, expect_invocations=1, expect_order=2)

        with serial(api, timeout=50, job_name_prefix=api.job_name_prefix, report_interval=1) as ctrl1:
            ctrl1.invoke_unchecked('j11_slow_unchecked')
            ctrl1.invoke('j12')


def test_invoke_unchecked_dont_wait_parallel(api_type):
    with api_select.api(__file__, api_type, login=True) as api:
        api.flow_job()
        api.job('j11_slow_unchecked', max_fails=0, expect_invocations=1, expect_order=1, exec_time=100, unknown_result=True)
        api.job('j12', max_fails=0, expect_invocations=1, expect_order=2, exec_time=5)

        with parallel(api, timeout=50, job_name_prefix=api.job_name_prefix, report_interval=1) as ctrl1:
            ctrl1.invoke_unchecked('j11_slow_unchecked')
            ctrl1.invoke('j12')


def test_invoke_unchecked_serial(api_type):
    with api_select.api(__file__, api_type, login=True) as api:
        api.job('j11_unchecked', max_fails=0, expect_invocations=1, expect_order=None, exec_time=30, unknown_result=True)
        api.job('j12', max_fails=0, expect_invocations=1, expect_order=1, exec_time=5)
        api.job('j13_unchecked', max_fails=0, expect_invocations=1, expect_order=2, exec_time=30, invocation_delay=0, unknown_result=True)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=1) as ctrl1:
            ctrl1.invoke_unchecked('j11_unchecked')
            ctrl1.invoke('j12')
            ctrl1.invoke_unchecked('j13_unchecked')


def test_invoke_unchecked_parallel(api_type):
    with api_select.api(__file__, api_type, login=True) as api:
        api.job('j11_unchecked', max_fails=0, expect_invocations=1, expect_order=None, exec_time=30, unknown_result=True)
        api.job('j12', max_fails=0, expect_invocations=1, expect_order=1, exec_time=5)
        api.job('j13_unchecked', max_fails=0, expect_invocations=1, expect_order=1)

        with parallel(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=1) as ctrl1:
            ctrl1.invoke_unchecked('j11_unchecked')
            ctrl1.invoke('j12')
            ctrl1.invoke_unchecked('j13_unchecked')


def test_invoke_unchecked_serial_fails(api_type):
    with api_select.api(__file__, api_type, login=True) as api:
        api.job('j11_unchecked', max_fails=0, expect_invocations=1, expect_order=None, exec_time=30, unknown_result=True)
        api.job('j12', max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j13_fail_unchecked', max_fails=1, expect_invocations=1, expect_order=2)
        api.job('j14', max_fails=0, expect_invocations=1, expect_order=2, exec_time=5)
        api.job('j15_unchecked', max_fails=0, expect_invocations=1, expect_order=None, exec_time=30, unknown_result=True)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=1) as ctrl1:
            ctrl1.invoke_unchecked('j11_unchecked')
            ctrl1.invoke('j12')
            ctrl1.invoke_unchecked('j13_fail_unchecked')
            ctrl1.invoke('j14')
            ctrl1.invoke_unchecked('j15_unchecked')


def test_invoke_unchecked_parallel_fails(api_type):
    with api_select.api(__file__, api_type, login=True) as api:
        api.job('j11_unchecked', max_fails=0, expect_invocations=1, expect_order=None, exec_time=30, unknown_result=True)
        api.job('j12', max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j13_fail_unchecked', max_fails=1, expect_invocations=1, expect_order=1)
        api.job('j14', max_fails=0, expect_invocations=1, expect_order=1, exec_time=5)
        api.job('j15_unchecked', max_fails=0, expect_invocations=1, expect_order=1)

        with parallel(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=1) as ctrl1:
            ctrl1.invoke_unchecked('j11_unchecked')
            ctrl1.invoke('j12')
            ctrl1.invoke_unchecked('j13_fail_unchecked')
            ctrl1.invoke('j14')
            ctrl1.invoke_unchecked('j15_unchecked')


def test_invoke_unchecked_mix_fails(api_type):
    with api_select.api(__file__, api_type, login=True) as api:
        api.flow_job()
        api.job('j11_unchecked', max_fails=0, expect_invocations=1, expect_order=None)
        api.job('j12', max_fails=0, expect_invocations=1, expect_order=2)
        api.job('j31', max_fails=0, expect_invocations=1, expect_order=3)
        # Make sure result is available during first invocation of _check, only way to hit error handling code in unchecked job
        vfast = 0.00000000000000000000000000000000001
        api.job('j32_fail_unchecked', max_fails=1, expect_invocations=1, expect_order=3, exec_time=vfast, invocation_delay=0)
        api.job('j33_slow_unchecked', max_fails=0, expect_invocations=1, expect_order=None, exec_time=100, unknown_result=True)
        api.job('j34', max_fails=0, expect_invocations=1, expect_order=3, exec_time=5)
        api.job('j35_fail_unchecked', max_fails=1, expect_invocations=1, expect_order=3)
        api.job('j13', max_fails=0, expect_invocations=1, expect_order=4)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=1) as ctrl1:
            ctrl1.invoke_unchecked('j11_unchecked')
            ctrl1.invoke('j12')

            with ctrl1.parallel(timeout=40, report_interval=3) as ctrl2:
                with ctrl2.serial(timeout=40, report_interval=3) as ctrl3a:
                    ctrl3a.invoke('j31')
                    ctrl3a.invoke_unchecked('j32_fail_unchecked')

                with ctrl2.parallel(timeout=40, report_interval=3) as ctrl3b:
                    ctrl3b.invoke_unchecked('j33_slow_unchecked')
                    ctrl3b.invoke('j34')
                    ctrl3b.invoke_unchecked('j35_fail_unchecked')

            ctrl1.invoke('j13')


def test_invoke_unchecked_mix_no_fails(api_type):
    with api_select.api(__file__, api_type, login=True) as api:
        api.job('j31_unchecked', max_fails=0, expect_invocations=1, expect_order=1, exec_time=30, unknown_result=True)
        api.job('j32_unchecked', max_fails=0, expect_invocations=1, expect_order=1, exec_time=30, unknown_result=True)
        api.job('j11', max_fails=0, expect_invocations=1, expect_order=2)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=1) as ctrl1:
            with ctrl1.parallel(timeout=40, report_interval=3) as ctrl2:
                with ctrl2.serial(timeout=40, report_interval=3) as ctrl3a:
                    ctrl3a.invoke_unchecked('j31_unchecked')

                with ctrl2.parallel(timeout=40, report_interval=3) as ctrl3b:
                    ctrl3b.invoke_unchecked('j32_unchecked')

            ctrl1.invoke('j11')
