# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from pytest import raises

from jenkinsflow.flow import serial, JobNotIdleException
from jenkinsflow.mocked import hyperspeed
from .cfg import ApiType
from .framework import api_select


def test_no_running_jobs():
    with api_select.api(__file__, login=True) as api:
        api.flow_job()
        api.job('j1', exec_time=50, max_fails=0, expect_invocations=1, expect_order=None, unknown_result=True)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix) as ctrl1:
            ctrl1.invoke_unchecked('j1')

        # Make sure job has actually started nefore entering new flow
        hyperspeed.sleep(1)

        with raises(JobNotIdleException) as exinfo:
            with serial(api, timeout=70, job_name_prefix=api.job_name_prefix) as ctrl1:
                ctrl1.invoke('j1')

        assert "job: 'jenkinsflow_test__no_running_jobs__j1' is in state RUNNING. It must be IDLE." in exinfo.value.message


def test_no_running_jobs_unchecked():
    with api_select.api(__file__, login=True) as api:
        api.flow_job()
        api.job('j1', exec_time=50, max_fails=0, expect_invocations=1, expect_order=None, unknown_result=True)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix) as ctrl1:
            ctrl1.invoke_unchecked('j1')

        hyperspeed.sleep(1)

        with raises(JobNotIdleException) as exinfo:
            with serial(api, timeout=70, job_name_prefix=api.job_name_prefix) as ctrl1:
                ctrl1.invoke_unchecked('j1')

        assert "unchecked job: 'jenkinsflow_test__no_running_jobs_unchecked__j1' is in state RUNNING. It must be IDLE." in exinfo.value.message


def test_no_running_jobs_jobs_allowed():
    with api_select.api(__file__, login=True) as api:
        api.flow_job()
        exp_invocations = 2 if api.api_type != ApiType.MOCK else 1
        unknown_result = False if api.api_type != ApiType.MOCK else True
        api.job('j1', exec_time=20, max_fails=0, expect_invocations=exp_invocations, expect_order=None, unknown_result=unknown_result)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix) as ctrl1:
            ctrl1.invoke_unchecked('j1')

        hyperspeed.sleep(1)

        # TODO
        if api.api_type != ApiType.MOCK:
            with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, require_idle=False) as ctrl1:
                ctrl1.invoke('j1')
