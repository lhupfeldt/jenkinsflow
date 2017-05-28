# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from pytest import raises

from jenkinsflow.flow import parallel, serial, FailedChildJobException, FailedChildJobsException
from .framework import api_select, utils


def test_retry_serial_toplevel(api_type):
    with api_select.api(__file__, api_type) as api:
        api.flow_job()
        api.job('j11', max_fails=0, expect_invocations=2, expect_order=1)
        api.job('j12_fail', max_fails=1, expect_invocations=2, expect_order=2, serial=True)
        api.job('j13', max_fails=0, expect_invocations=1, expect_order=3, serial=True)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, max_tries=2) as ctrl1:
            ctrl1.invoke('j11')
            ctrl1.invoke('j12_fail')
            ctrl1.invoke('j13')


def test_retry_serial_toplevel_fail(api_type):
    with api_select.api(__file__, api_type) as api:
        api.flow_job()
        api.job('j11', max_fails=0, expect_invocations=2, expect_order=1)
        api.job('j12_fail', max_fails=2, expect_invocations=2, expect_order=2, serial=True)
        api.job('j13', max_fails=0, expect_invocations=0, expect_order=None)

        with raises(FailedChildJobException):
            with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, max_tries=2) as ctrl1:
                ctrl1.invoke('j11')
                ctrl1.invoke('j12_fail')
                ctrl1.invoke('j13')


def test_retry_parallel_toplevel(api_type):
    with api_select.api(__file__, api_type) as api:
        api.flow_job()
        api.job('j11', max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j12_fail', max_fails=1, expect_invocations=2, expect_order=1)
        api.job('j13', max_fails=0, expect_invocations=1, expect_order=1)

        with parallel(api, timeout=70, job_name_prefix=api.job_name_prefix, max_tries=2) as ctrl1:
            ctrl1.invoke('j11')
            ctrl1.invoke('j12_fail')
            ctrl1.invoke('j13')


def test_retry_parallel_toplevel_fail(api_type):
    with api_select.api(__file__, api_type) as api:
        api.flow_job()
        api.job('j11', max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j12_fail', max_fails=2, expect_invocations=2, expect_order=1)
        api.job('j13', max_fails=0, expect_invocations=1, expect_order=1)

        with raises(FailedChildJobsException):
            with parallel(api, timeout=70, job_name_prefix=api.job_name_prefix, max_tries=2) as ctrl1:
                ctrl1.invoke('j11')
                ctrl1.invoke('j12_fail')
                ctrl1.invoke('j13')


def test_retry_serial_inner(api_type):
    with api_select.api(__file__, api_type) as api:
        api.flow_job()
        api.job('j11', max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j21', max_fails=0, expect_invocations=2, expect_order=2, serial=True)
        api.job('j22_fail', max_fails=1, expect_invocations=2, expect_order=3, serial=True)
        api.job('j23', max_fails=0, expect_invocations=1, expect_order=4, serial=True)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix) as ctrl1:
            ctrl1.invoke('j11')
            with ctrl1.serial(max_tries=2) as ctrl2:
                ctrl2.invoke('j21')
                ctrl2.invoke('j22_fail')
                ctrl2.invoke('j23')


def test_retry_parallel_inner(api_type):
    with api_select.api(__file__, api_type) as api:
        api.flow_job()
        api.job('j11', max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j21', max_fails=0, expect_invocations=1, expect_order=2)
        api.job('j22_fail', max_fails=1, expect_invocations=2, expect_order=2)
        api.job('j23', max_fails=0, expect_invocations=1, expect_order=2)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix) as ctrl1:
            ctrl1.invoke('j11')
            with ctrl1.parallel(max_tries=2) as ctrl2:
                ctrl2.invoke('j21')
                ctrl2.invoke('j22_fail')
                ctrl2.invoke('j23')


def test_retry_serial_through_parent_serial_level(api_type):
    with api_select.api(__file__, api_type) as api:
        api.flow_job()
        api.job('j11', max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j21', max_fails=0, expect_invocations=2, expect_order=2, serial=True)
        api.job('j31_fail', max_fails=2, expect_invocations=3, expect_order=3, serial=True)
        api.job('j32', max_fails=0, expect_invocations=1, expect_order=4, serial=True)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix) as ctrl1:
            ctrl1.invoke('j11')
            with ctrl1.serial(timeout=70, max_tries=2) as ctrl2:
                ctrl2.invoke('j21')
                with ctrl2.serial(timeout=70, max_tries=2) as ctrl3:
                    ctrl3.invoke('j31_fail')
                    ctrl3.invoke('j32')


def test_retry_serial_through_parent_serial_level_fail(api_type):
    with api_select.api(__file__, api_type) as api:
        api.flow_job()
        api.job('j31_fail', max_fails=4, expect_invocations=4, expect_order=1)
        api.job('j32', max_fails=0, expect_invocations=0, expect_order=None)

        with raises(FailedChildJobException):
            with serial(api, timeout=70, job_name_prefix=api.job_name_prefix) as ctrl1:
                with ctrl1.serial(timeout=70, max_tries=2) as ctrl2:
                    with ctrl2.serial(timeout=70, max_tries=2) as ctrl3:
                        ctrl3.invoke('j31_fail')
                        ctrl3.invoke('j32')


def test_retry_serial_through_parent_parallel_level(api_type):
    with api_select.api(__file__, api_type) as api:
        api.flow_job()
        api.job('j11', max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j21', max_fails=0, expect_invocations=1, expect_order=2, serial=True)
        api.job('j31_fail', max_fails=2, expect_invocations=3, expect_order=2)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix) as ctrl1:
            ctrl1.invoke('j11')
            with ctrl1.parallel(timeout=70, max_tries=2) as ctrl2:
                ctrl2.invoke('j21')
                with ctrl2.serial(timeout=70, max_tries=2) as ctrl3:
                    ctrl3.invoke('j31_fail')


def test_retry_serial_through_parent_parallel_level_fail(api_type):
    with api_select.api(__file__, api_type) as api:
        api.flow_job()
        api.job('j31_fail', max_fails=4, expect_invocations=4, expect_order=1)

        with raises(FailedChildJobException):
            with serial(api, timeout=70, job_name_prefix=api.job_name_prefix) as ctrl1:
                with ctrl1.parallel(timeout=70, max_tries=2) as ctrl2:
                    with ctrl2.serial(timeout=70, max_tries=2) as ctrl3:
                        ctrl3.invoke('j31_fail')


def test_retry_parallel_through_parent_serial_level(api_type):
    with api_select.api(__file__, api_type) as api:
        api.flow_job()
        api.job('j11', max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j21', max_fails=0, expect_invocations=2, expect_order=2)
        api.job('j31_fail', max_fails=2, expect_invocations=3, expect_order=3)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix) as ctrl1:
            ctrl1.invoke('j11')
            with ctrl1.serial(timeout=70, max_tries=2) as ctrl2:
                ctrl2.invoke('j21')
                with ctrl2.parallel(timeout=70, max_tries=2) as ctrl3:
                    ctrl3.invoke('j31_fail')


def test_retry_parallel_through_parent_parallel_level(api_type):
    with api_select.api(__file__, api_type) as api:
        api.flow_job()
        api.job('j11', max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j21', max_fails=0, expect_invocations=1, expect_order=2, serial=True)
        api.job('j22_fail', max_fails=1, expect_invocations=2, expect_order=2)
        api.job('j31_fail', max_fails=2, expect_invocations=3, expect_order=2)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix) as ctrl1:
            ctrl1.invoke('j11')
            with ctrl1.parallel(timeout=70, max_tries=2) as ctrl2:
                ctrl2.invoke('j21')
                ctrl2.invoke('j22_fail')
                with ctrl2.parallel(timeout=70, max_tries=2) as ctrl3:
                    ctrl3.invoke('j31_fail')


def test_retry_parallel_through_outer_level(api_type, capsys):
    with api_select.api(__file__, api_type) as api:
        api.flow_job()
        api.job('j11', max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j21', max_fails=0, expect_invocations=1, expect_order=2, serial=True)
        api.job('j31', max_fails=0, expect_invocations=1, expect_order=3, serial=True)
        api.job('j41_fail', max_fails=2, expect_invocations=3, expect_order=3)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix) as ctrl1:
            ctrl1.invoke('j11')
            with ctrl1.serial(timeout=70, max_tries=2) as ctrl2:
                ctrl2.invoke('j21')
                with ctrl2.parallel(timeout=70) as ctrl3:
                    ctrl3.invoke('j31')
                    with ctrl3.parallel(timeout=70, max_tries=2) as ctrl4:
                        ctrl4.invoke('j41_fail')

        sout, _ = capsys.readouterr()
        sout = utils.replace_host_port(api_type, sout)
        assert "RETRY: job: 'jenkinsflow_test__retry_parallel_through_outer_level__j41_fail' failed but will be retried. Up to 1 more times in current flow" in sout, 'SOUT:' + sout
        assert "RETRY: job: 'jenkinsflow_test__retry_parallel_through_outer_level__j41_fail' failed but will be retried. Up to 2 more times through outer flow" in sout, 'SOUT:' + sout


def test_retry_serial_through_outer_level(api_type):
    with api_select.api(__file__, api_type) as api:
        api.flow_job()
        api.job('j11', max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j21', max_fails=0, expect_invocations=1, expect_order=2, serial=True)
        api.job('j31', max_fails=0, expect_invocations=1, expect_order=3, serial=True)
        api.job('j41', max_fails=0, expect_invocations=4, expect_order=3)
        api.job('j42_fail', max_fails=3, expect_invocations=4, expect_order=3, serial=True)
        api.job('j43', max_fails=0, expect_invocations=1, expect_order=3, serial=True)

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


def test_retry_mix(api_type):
    with api_select.api(__file__, api_type) as api:
        api.flow_job()
        api.job('j11_fail', max_fails=1, expect_invocations=2, expect_order=1)
        api.job('j12', max_fails=0, expect_invocations=1, expect_order=2, serial=True)
        api.job('j21', max_fails=0, expect_invocations=1, expect_order=3, serial=True)
        api.job('j22_fail', max_fails=2, expect_invocations=3, expect_order=3)
        api.job('j31_fail', max_fails=3, expect_invocations=4, expect_order=3)
        api.job('j32', max_fails=0, expect_invocations=1, expect_order=3, serial=True)
        api.job('j23', max_fails=0, expect_invocations=1, expect_order=3)
        api.job('j13', max_fails=0, expect_invocations=1, expect_order=4, serial=True)

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
