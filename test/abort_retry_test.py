# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import os

import pytest
from pytest import raises

from jenkinsflow.flow import parallel, serial, FailedChildJobException, FailedChildJobsException

from .framework import api_select
from .framework.abort_job import abort
from .cfg import ApiType

here = os.path.abspath(os.path.dirname(__file__))


@pytest.mark.not_apis(ApiType.SCRIPT)
def test_abort_retry_serial_toplevel(api_type):
    with api_select.api(__file__, api_type) as api:
        api.flow_job()
        api.job('j11', max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j12_abort', max_fails=0, expect_invocations=1, expect_order=2, exec_time=20, serial=True, final_result='ABORTED')
        api.job('j13', max_fails=0, expect_invocations=0, expect_order=None, serial=True)

        abort(api, 'j12_abort', 10)

        with raises(FailedChildJobException):
            with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, max_tries=2) as ctrl1:
                ctrl1.invoke('j11')
                ctrl1.invoke('j12_abort')
                ctrl1.invoke('j13')


@pytest.mark.not_apis(ApiType.SCRIPT)
def test_abort_retry_parallel_toplevel(api_type):
    with api_select.api(__file__, api_type) as api:
        api.flow_job()
        api.job('j11', max_fails=0, expect_invocations=1, expect_order=None)
        api.job('j12_abort', max_fails=0, expect_invocations=1, expect_order=None, exec_time=20, final_result='ABORTED')
        api.job('j13', max_fails=0, expect_invocations=1, expect_order=None)

        abort(api, 'j12_abort', 10)

        with raises(FailedChildJobsException):
            with parallel(api, timeout=70, job_name_prefix=api.job_name_prefix, max_tries=2) as ctrl1:
                ctrl1.invoke('j11')
                ctrl1.invoke('j12_abort')
                ctrl1.invoke('j13')


@pytest.mark.not_apis(ApiType.SCRIPT)
def test_abort_retry_serial_parallel_nested(api_type):
    with api_select.api(__file__, api_type) as api:
        api.flow_job()
        api.job('j11', max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j21', max_fails=0, expect_invocations=1, expect_order=2, exec_time=20)
        api.job('j22_abort', max_fails=0, expect_invocations=1, expect_order=2, exec_time=20, final_result='ABORTED')
        api.job('j23', max_fails=0, expect_invocations=1, expect_order=2, exec_time=5)
        api.job('j24', max_fails=0, expect_invocations=1, expect_order=2)
        api.job('j12', max_fails=0, expect_invocations=0, expect_order=None, serial=True)

        abort(api, 'j22_abort', 10)

        with raises(FailedChildJobException):
            with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, max_tries=2) as sctrl1:
                sctrl1.invoke('j11')
                with sctrl1.parallel() as pctrl1:
                    pctrl1.invoke('j21')
                    pctrl1.invoke('j22_abort')
                    pctrl1.invoke('j23')
                    pctrl1.invoke('j24')
                sctrl1.invoke('j12')


@pytest.mark.not_apis(ApiType.SCRIPT)
def test_abort_retry_parallel_serial_nested(api_type):
    with api_select.api(__file__, api_type) as api:
        api.flow_job()
        api.job('j11', max_fails=0, expect_invocations=1, expect_order=None)
        api.job('j21', max_fails=0, expect_invocations=1, expect_order=None)
        api.job('j22_abort', max_fails=0, expect_invocations=1, expect_order=None, exec_time=20, final_result='ABORTED')
        api.job('j23', max_fails=0, expect_invocations=0, expect_order=None)
        api.job('j24', max_fails=0, expect_invocations=0, expect_order=None)
        api.job('j12', max_fails=0, expect_invocations=1, expect_order=1, serial=True)

        abort(api, 'j22_abort', 10)

        with raises(FailedChildJobsException):
            with parallel(api, timeout=70, job_name_prefix=api.job_name_prefix, max_tries=2) as sctrl1:
                sctrl1.invoke('j11')
                with sctrl1.serial() as pctrl1:
                    pctrl1.invoke('j21')
                    pctrl1.invoke('j22_abort')
                    pctrl1.invoke('j23')
                    pctrl1.invoke('j24')
                sctrl1.invoke('j12')
