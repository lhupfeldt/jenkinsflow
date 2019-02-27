# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import os, time, re

import pytest
from pytest import raises, xfail

from jenkinsflow.flow import serial, FailedChildJobException, FinalResultException, BuildResult

from .cfg import ApiType
from .framework import api_select
from .framework.utils import lines_in, kill_current_msg
from .framework.killer import kill

here = os.path.abspath(os.path.dirname(__file__))


@pytest.mark.not_apis(ApiType.SCRIPT)  # TODO
def test_kill_all_unchecked(api_type, capsys):
    with api_select.api(__file__, api_type, login=True) as api:
        api.flow_job()
        api.job('j1', max_fails=0, expect_invocations=1, expect_order=None, exec_time=50, invocation_delay=0, unknown_result=False, kill=True)
        api.job('j2', max_fails=0, expect_invocations=1, expect_order=1, invocation_delay=0, unknown_result=False, kill=True)
        api.job('j3', max_fails=0, expect_invocations=3, expect_order=None, exec_time=50, invocation_delay=0, unknown_result=False, kill=True, allow_running=True)
        api.job('j4', max_fails=0, expect_invocations=1, expect_order=None, invocation_delay=0, unknown_result=False, kill=True)
        api.job('j5', max_fails=1, expect_invocations=1, expect_order=2, invocation_delay=0, unknown_result=False, kill=True)

        def flow(api, kill_all):
            with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, kill_all=kill_all) as ctrl1:
                with ctrl1.parallel() as ctrl2:
                    ctrl2.invoke_unchecked('j1')
                    ctrl2.invoke_unchecked('j2')
                with ctrl1.parallel() as ctrl3:
                    ctrl3.invoke_unchecked('j3')
                    ctrl3.invoke_unchecked('j3') # Queue
                    ctrl3.invoke_unchecked('j3') # Queue
                    ctrl3.invoke_unchecked('j4')
                    ctrl3.invoke_unchecked('j5')

        # Invoke the flow
        flow(api, False)

        # Make sure job has actually started before entering new flow
        api.sleep(5)

        if capsys:
            sout, _ = capsys.readouterr()
            assert lines_in(api_type, sout, "unchecked job: 'jenkinsflow_test__kill_all_unchecked__j1' UNKNOWN - RUNNING")
            assert lines_in(api_type, sout, "unchecked job: 'jenkinsflow_test__kill_all_unchecked__j3' Invocation-1 UNKNOWN - RUNNING")

        # Kill the flow
        flow(api, True)

        if not capsys:
            # Not called by pytest, but from flow hudson job
            return

        sout, _ = capsys.readouterr()
        assert lines_in(
            api_type, sout,
            "^Killing all running builds for: 'jenkinsflow_test__kill_all_unchecked__j1'",
            "job: 'jenkinsflow_test__kill_all_unchecked__j1' stopped running",
            "job: 'jenkinsflow_test__kill_all_unchecked__j1' Status IDLE - build: ",
            "^ABORTED: 'jenkinsflow_test__kill_all_unchecked__j1'",
            "^--- Final status ---",
            "^serial flow: [",
            "^   parallel flow: (",
            "^      unchecked job: 'jenkinsflow_test__kill_all_unchecked__j1' ABORTED - IDLE",
            "^      unchecked job: 'jenkinsflow_test__kill_all_unchecked__j2' SUCCESS - IDLE",
            "^   )",

            "^   parallel flow: (",
            "^      unchecked job: 'jenkinsflow_test__kill_all_unchecked__j3' Invocation-1 ABORTED - IDLE",
            "^      unchecked job: 'jenkinsflow_test__kill_all_unchecked__j3' Invocation-2 ABORTED - IDLE",
            "^      unchecked job: 'jenkinsflow_test__kill_all_unchecked__j3' Invocation-3 ABORTED - IDLE",
            "^      unchecked job: 'jenkinsflow_test__kill_all_unchecked__j4' SUCCESS - IDLE",
            "^      unchecked job: 'jenkinsflow_test__kill_all_unchecked__j5' FAILURE - IDLE",
            "^   )",
            "^]",
        )


@pytest.mark.not_apis(ApiType.MOCK, ApiType.SCRIPT)
def test_kill_mini(api_type, capsys):
    """Cut down kill_current for debugging"""
    with api_select.api(__file__, api_type, login=True) as api:
        is_hudson = os.environ.get('HUDSON_URL')
        if is_hudson:  # TODO investigate why this test fails in Hudson
            xfail("Doesn't pass in Hudson")
            return

        api.flow_job()
        num_j6_invocations = 2
        api.job('j6', max_fails=0, expect_invocations=num_j6_invocations, expect_order=None, exec_time=50, kill=True,
                num_builds_to_keep=num_j6_invocations*2 + 1, params=(('a', 0, 'integer'),))

        kill(api, 35, 1)

        with raises(FinalResultException) as exinfo:
            with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=0.05) as ctrl1:
                with ctrl1.parallel() as ctrl2:
                    for ii in range(0, num_j6_invocations):
                         # Queue a lot of jobs
                        ctrl2.invoke('j6', a=ii)

        assert exinfo.value.result == BuildResult.FAILURE  # TODO? Note that ABORTED on child job propagates as FAILURE to the flow

        if not capsys:
            return

        sout, _ = capsys.readouterr()
        assert lines_in(
            api_type, sout,
            "^Got SIGTERM: Killing all builds belonging to current flow",
            "^--- Final status ---",
            "^serial flow: [",
            "^   parallel flow: (",
            re.compile("      job: 'jenkinsflow_test__kill_mini__j6' Invocation-[0-9]+ ABORTED - IDLE"),
            re.compile("      job: 'jenkinsflow_test__kill_mini__j6' Invocation-[0-9]+ DEQUEUED - IDLE"),
            "^   )",
            "^",
            "^]"
        )


@pytest.mark.not_apis(ApiType.MOCK, ApiType.SCRIPT)  # TODO
def test_kill_current(api_type, capsys):
    with api_select.api(__file__, api_type, login=True) as api:
        is_hudson = os.environ.get('HUDSON_URL')
        if is_hudson:  # TODO investigate why this test fails in Hudson
            xfail("Doesn't pass in Hudson")
            return

        api.flow_job()
        api.job('j1', max_fails=0, expect_invocations=1, expect_order=None, exec_time=50, kill=True)
        api.job('j2', max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j3', max_fails=0, expect_invocations=1, expect_order=None, exec_time=50, kill=True)
        api.job('j4', max_fails=1, expect_invocations=1, expect_order=2)
        api.job('j5', max_fails=0, expect_invocations=1, expect_order=None, exec_time=50, kill=True)

        num_j6_invocations = 20
        api.job('j6', max_fails=0, expect_invocations=num_j6_invocations, expect_order=None, exec_time=50, kill=True,
                num_builds_to_keep=num_j6_invocations*2 + 1, params=(('a', 0, 'integer'),))
        api.job('j7', max_fails=0, expect_invocations=0, expect_order=None, exec_time=50)

        # Set a long sleep here, when heaviliy loaded it can take time for the flow to get started
        kill(api, 35, 1)

        # TODO: shouldn't we expect a FailedChildJobsException here?
        with raises(FinalResultException) as exinfo:
            with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=0.05) as ctrl1:
                with ctrl1.parallel() as ctrl2:
                    ctrl2.invoke('j1')
                    with ctrl2.serial() as ctrl3:
                        ctrl3.invoke('j2')
                        ctrl3.invoke('j3')
                    ctrl2.invoke('j4')
                    ctrl2.invoke_unchecked('j5')
                    for ii in range(0, num_j6_invocations):
                         # Queue a lot of jobs
                        ctrl2.invoke('j6', a=ii)
                with ctrl1.parallel() as ctrl4:
                    ctrl4.invoke('j7')

        assert exinfo.value.result == BuildResult.FAILURE  # TODO? Note that ABORTED on child job propagates as FAILURE to the flow

        if not capsys:
            return

        sout, _ = capsys.readouterr()
        assert lines_in(
            api_type, sout,
            "^Got SIGTERM: Killing all builds belonging to current flow",
            kill_current_msg(api, 'jenkinsflow_test__kill_current__j1', 1),
            kill_current_msg(api, 'jenkinsflow_test__kill_current__j3', 1),
            kill_current_msg(api, 'jenkinsflow_test__kill_current__j5', 1),
            "^--- Final status ---",
            "^serial flow: [",
            "^   parallel flow: (",
            "^      job: 'jenkinsflow_test__kill_current__j1' ABORTED - IDLE",
            "^      serial flow: [",
            "^         job: 'jenkinsflow_test__kill_current__j2' SUCCESS - IDLE",
            "^         job: 'jenkinsflow_test__kill_current__j3' ABORTED - IDLE",
            "^      ]",
            "^      job: 'jenkinsflow_test__kill_current__j4' FAILURE - IDLE",
            "^      unchecked job: 'jenkinsflow_test__kill_current__j5' ABORTED - IDLE",
            re.compile("      job: 'jenkinsflow_test__kill_current__j6' Invocation-[0-9]+ ABORTED - IDLE"),
            re.compile("      job: 'jenkinsflow_test__kill_current__j6' Invocation-[0-9]+ DEQUEUED - IDLE"),
            "^   )",
            "^",
            "^   parallel flow: (",
            "^      job: 'jenkinsflow_test__kill_current__j7' UNKNOWN - IDLE",
            "^   )",
            "^",
            "^]"
        )


@pytest.mark.not_apis(ApiType.MOCK, ApiType.SCRIPT)  # TODO
def test_kill_all_unchecked_no_job(api_type, capsys):
    with api_select.api(__file__, api_type, login=True) as api:
        api.flow_job()
        api.job('j1', max_fails=0, expect_invocations=1, expect_order=None, exec_time=50, unknown_result=False, kill=True)
        api.job('j2', max_fails=0, expect_invocations=1, expect_order=1, unknown_result=False, kill=True)
        #api.job('j3', 0, 0, None, non_existing=True)
        api.job('j4', max_fails=0, expect_invocations=1, expect_order=1, unknown_result=False, kill=True)
        #api.job('j5', 0, 0, None, non_existing=True)

        def flow(api, kill_all, allow_missing_jobs):
            with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, allow_missing_jobs=allow_missing_jobs, kill_all=kill_all) as ctrl1:
                with ctrl1.parallel() as ctrl2:
                    ctrl2.invoke_unchecked('j1')
                    ctrl2.invoke_unchecked('j2')
                with ctrl1.parallel() as ctrl3:
                    ctrl3.invoke('j3')
                    ctrl3.invoke('j4')
                    ctrl3.invoke('j5')

        # Invoke the flow
        with raises(FailedChildJobException):
            flow(api, False, True)

        # Make sure job has actually started before entering new flow
        api.sleep(5)

        if capsys:
            sout, _ = capsys.readouterr()
            assert lines_in(api_type, sout, "unchecked job: 'jenkinsflow_test__kill_all_unchecked_no_job__j1' UNKNOWN - RUNNING")
            assert lines_in(api_type, sout, "job: 'jenkinsflow_test__kill_all_unchecked_no_job__j3' - MISSING JOB")

        # Kill the flow
        flow(api, True, False)

        if not capsys:
            return

        sout, _ = capsys.readouterr()
        assert lines_in(
            api_type, sout,
            "^Killing all running builds for: 'jenkinsflow_test__kill_all_unchecked_no_job__j1'",
            "job: 'jenkinsflow_test__kill_all_unchecked_no_job__j1' stopped running",
            "job: 'jenkinsflow_test__kill_all_unchecked_no_job__j1' Status IDLE - build: ",
            "^ABORTED: 'jenkinsflow_test__kill_all_unchecked_no_job__j1'",
            "^--- Final status ---",
            "^serial flow: [",
            "^   parallel flow: (",
            "^      unchecked job: 'jenkinsflow_test__kill_all_unchecked_no_job__j1' ABORTED - IDLE",
            "^      unchecked job: 'jenkinsflow_test__kill_all_unchecked_no_job__j2' SUCCESS - IDLE",
            "^   )",

            "^   parallel flow: (",
            "^      job: 'jenkinsflow_test__kill_all_unchecked_no_job__j3' - MISSING JOB",
            "^      job: 'jenkinsflow_test__kill_all_unchecked_no_job__j4' SUCCESS - IDLE",
            "^      job: 'jenkinsflow_test__kill_all_unchecked_no_job__j5' - MISSING JOB",
            "^   )",
            "^]",
        )
