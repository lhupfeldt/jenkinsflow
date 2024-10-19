# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from datetime import datetime
from pytest import raises

from jenkinsflow.flow import serial, JobNotIdleException

from .framework import api_select
from .framework.utils import lines_in
from .framework.cfg import ApiType


def _wait_for_job_to_start(api, name):
    if api.api_type == ApiType.SCRIPT:
        return

    # Make sure job has started. Because it may be queued?
    # TODO: Wait until it is started, no 'hard' sleep.
    api.sleep(1)


def test_no_running_jobs(api_type, capsys):
    with api_select.api(__file__, api_type, login=True) as api:
        api.flow_job()
        api.job('j1', max_fails=0, expect_invocations=1, expect_order=None, exec_time=50, invocation_delay=0, unknown_result=True)

        print("Starting first flow:", datetime.now())
        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix) as ctrl1:
            ctrl1.invoke_unchecked('j1')
        print("Finished first flow:", datetime.now())

        sout, serr = capsys.readouterr()
        assert lines_in(api_type, sout, "unchecked job: 'jenkinsflow_test__no_running_jobs__j1' UNKNOWN - RUNNING")
        print(sout)
        print(serr)

        _wait_for_job_to_start(api, "j1")

        print("Starting second flow:", datetime.now())
        with raises(JobNotIdleException) as exinfo:
            with serial(api, timeout=70, job_name_prefix=api.job_name_prefix) as ctrl1:
                ctrl1.invoke('j1')
        print("Finished second flow:", datetime.now())

        assert "job: 'jenkinsflow_test__no_running_jobs__j1' is in state RUNNING. It must be IDLE." in str(exinfo.value)


def test_no_running_jobs_unchecked(api_type, capsys):
    with api_select.api(__file__, api_type, login=True) as api:
        api.flow_job()
        api.job('j1', max_fails=0, expect_invocations=1, expect_order=None, exec_time=50, invocation_delay=0, unknown_result=True)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix) as ctrl1:
            ctrl1.invoke_unchecked('j1')

        sout, _ = capsys.readouterr()
        assert lines_in(api_type, sout, "unchecked job: 'jenkinsflow_test__no_running_jobs_unchecked__j1' UNKNOWN - RUNNING")

        _wait_for_job_to_start(api, "j1")

        print("second run")
        with raises(JobNotIdleException) as exinfo:
            with serial(api, timeout=70, job_name_prefix=api.job_name_prefix) as ctrl1:
                ctrl1.invoke_unchecked('j1')

        assert "unchecked job: 'jenkinsflow_test__no_running_jobs_unchecked__j1' is in state RUNNING. It must be IDLE." in str(exinfo.value)


def test_no_running_jobs_jobs_allowed(api_type):
    with api_select.api(__file__, api_type, login=True) as api:
        api.flow_job()
        exp_invocations = 2 if api.api_type != ApiType.MOCK else 1
        unknown_result = False if api.api_type != ApiType.MOCK else True
        api.job('j1', max_fails=0, expect_invocations=exp_invocations, expect_order=None, exec_time=20,
                invocation_delay=0, unknown_result=unknown_result)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix) as ctrl1:
            ctrl1.invoke_unchecked('j1')

        _wait_for_job_to_start(api, "j1")

        # TODO
        if api.api_type != ApiType.MOCK:
            with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, require_idle=False) as ctrl1:
                ctrl1.invoke('j1')
