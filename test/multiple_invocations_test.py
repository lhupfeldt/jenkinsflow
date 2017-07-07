# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import os, re

import pytest
from pytest import xfail

from jenkinsflow.flow import serial, parallel
from .cfg import ApiType
from .framework import api_select
from .framework.utils import lines_in, build_started_msg


def test_multiple_invocations_serial_same_flow(api_type):
    with api_select.api(__file__, api_type) as api:
        api.flow_job()
        _params = (('password', '', 'Some password'), ('s1', '', 'Some string argument'))
        api.job('j1', max_fails=0, expect_invocations=2, expect_order=1, params=_params)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=1) as ctrl1:
            ctrl1.invoke('j1', password='a', s1='b')
            ctrl1.invoke('j1', password='something else', s1='asdasdasdasdad')


def test_multiple_invocations_serial_same_flow_same_args(api_type):
    with api_select.api(__file__, api_type) as api:
        api.flow_job()
        _params = (('password', '', 'Some password'), ('s1', '', 'Some string argument'))
        api.job('j1', max_fails=0, expect_invocations=2, expect_order=1, params=_params)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=1) as ctrl1:
            ctrl1.invoke('j1', password='a', s1='b')
            ctrl1.invoke('j1', password='a', s1='b')


def test_multiple_invocations_new_flow(api_type):
    with api_select.api(__file__, api_type) as api:
        api.flow_job()
        _params = (('password', '', 'Some password'), ('s1', '', 'Some string argument'))
        api.job('j1', max_fails=0, expect_invocations=2, expect_order=1, params=_params)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=1) as ctrl1:
            ctrl1.invoke('j1', password='a', s1='b')

        with serial(api, timeout=15, job_name_prefix=api.job_name_prefix, report_interval=1) as ctrl1:
            ctrl1.invoke('j1', password='something else', s1='asdasdasdasdad')


def test_multiple_invocations_new_flow_same_args(api_type):
    with api_select.api(__file__, api_type) as api:
        api.flow_job()
        _params = (('password', '', 'Some password'), ('s1', '', 'Some string argument'))
        api.job('j1', max_fails=0, expect_invocations=2, expect_order=1, params=_params)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=1) as ctrl1:
            ctrl1.invoke('j1', password='a', s1='b')

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=1) as ctrl1:
            ctrl1.invoke('j1', password='a', s1='b')


@pytest.mark.not_apis(ApiType.MOCK, ApiType.SCRIPT)
def test_multiple_invocations_parallel_same_flow_queued(api_type, capsys):
    with api_select.api(__file__, api_type) as api:
        is_hudson = os.environ.get('HUDSON_URL')
        if is_hudson:  # TODO investigate why this test fails in Hudson
            xfail("Doesn't pass when using Hudson")
            return

        api.flow_job()
        _params = (('password', '', 'Some password'), ('s1', '', 'Some string argument'))
        api.job('j1', max_fails=0, expect_invocations=3, expect_order=1, exec_time=3, params=_params)

        with parallel(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=1) as ctrl1:
            ctrl1.invoke('j1', password='a', s1='invocation1')
            ctrl1.invoke('j1', password='b', s1='invocation2')
            ctrl1.invoke('j1', password='b', s1='invocation3')

        sout, _ = capsys.readouterr()
        assert lines_in(
            api_type, sout,
            "^Job Invocation-1 (1/1,1/1): http://x.x/job/jenkinsflow_test__multiple_invocations_parallel_same_flow_queued__j1",
            "^Job Invocation-2 (1/1,1/1): http://x.x/job/jenkinsflow_test__multiple_invocations_parallel_same_flow_queued__j1",
            "^Job Invocation-3 (1/1,1/1): http://x.x/job/jenkinsflow_test__multiple_invocations_parallel_same_flow_queued__j1",
            (
                build_started_msg(api, "jenkinsflow_test__multiple_invocations_parallel_same_flow_queued__j1", 1, invocation_number=1),
                "^job: 'jenkinsflow_test__multiple_invocations_parallel_same_flow_queued__j1' Invocation-1 stopped running",
                "^job: 'jenkinsflow_test__multiple_invocations_parallel_same_flow_queued__j1' Invocation-1 Status IDLE - build: #",
                "^SUCCESS: 'jenkinsflow_test__multiple_invocations_parallel_same_flow_queued__j1' Invocation-1",

                build_started_msg(api, "jenkinsflow_test__multiple_invocations_parallel_same_flow_queued__j1", 2, invocation_number=2),
                "^job: 'jenkinsflow_test__multiple_invocations_parallel_same_flow_queued__j1' Invocation-2 stopped running",
                "^job: 'jenkinsflow_test__multiple_invocations_parallel_same_flow_queued__j1' Invocation-2 Status IDLE - build: #",
                "^SUCCESS: 'jenkinsflow_test__multiple_invocations_parallel_same_flow_queued__j1' Invocation-2",

                build_started_msg(api, "jenkinsflow_test__multiple_invocations_parallel_same_flow_queued__j1", 3, invocation_number=3),
                "^job: 'jenkinsflow_test__multiple_invocations_parallel_same_flow_queued__j1' Invocation-3 stopped running",
                "^job: 'jenkinsflow_test__multiple_invocations_parallel_same_flow_queued__j1' Invocation-3 Status IDLE - build: #",
                "^SUCCESS: 'jenkinsflow_test__multiple_invocations_parallel_same_flow_queued__j1' Invocation-3",
            ),
            "^parallel flow: (",
            "job: 'jenkinsflow_test__multiple_invocations_parallel_same_flow_queued__j1' Invocation-1 SUCCESS",
            "job: 'jenkinsflow_test__multiple_invocations_parallel_same_flow_queued__j1' Invocation-2 SUCCESS",
            "job: 'jenkinsflow_test__multiple_invocations_parallel_same_flow_queued__j1' Invocation-3 SUCCESS",
            "^)",
        )


@pytest.mark.not_apis(ApiType.MOCK, ApiType.SCRIPT)
def test_multiple_invocations_parallel_same_flow_no_args_singlequeued(api_type, capsys):
    """
    Jenkins automatically throws away queued builds of parameterless jobs when another build is invoked,
    so that a max of one build can be queued
    """

    with api_select.api(__file__, api_type) as api:
        is_hudson = os.environ.get('HUDSON_URL')
        if is_hudson:  # TODO investigate why this test fails in Hudson
            xfail("Doesn't pass in Hudson")
            return

        api.flow_job()
        num_inv = 20
        api.job('j1', max_fails=0, expect_invocations=num_inv, expect_order=1, exec_time=15)

        with parallel(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=0.1, poll_interval=0.1) as ctrl1:
            for _ in range(0, num_inv):
                ctrl1.invoke('j1')

        sout, _ = capsys.readouterr()

        any_superseeded = re.compile(" +job: 'jenkinsflow_test__multiple_invocations_parallel_same_flow_no_args_singlequeued__j1' Invocation-[0-9]+ SUPERSEDED")
        assert lines_in(
            api_type, sout,
            "^Job Invocation-1 (1/1,1/1): http://x.x/job/jenkinsflow_test__multiple_invocations_parallel_same_flow_no_args_singlequeued__j1",
            "^Job Invocation-5 (1/1,1/1): http://x.x/job/jenkinsflow_test__multiple_invocations_parallel_same_flow_no_args_singlequeued__j1",
            "^Job Invocation-{} (1/1,1/1): http://x.x/job/jenkinsflow_test__multiple_invocations_parallel_same_flow_no_args_singlequeued__j1".format(num_inv),
            (
                build_started_msg(api, "jenkinsflow_test__multiple_invocations_parallel_same_flow_no_args_singlequeued__j1", 1, invocation_number=1),
                "^SUPERSEDED: 'jenkinsflow_test__multiple_invocations_parallel_same_flow_no_args_singlequeued__j1'",
                "^SUPERSEDED: 'jenkinsflow_test__multiple_invocations_parallel_same_flow_no_args_singlequeued__j1'",
                "^job: 'jenkinsflow_test__multiple_invocations_parallel_same_flow_no_args_singlequeued__j1' Invocation-1 Status RUNNING - build:",
                "^job: 'jenkinsflow_test__multiple_invocations_parallel_same_flow_no_args_singlequeued__j1' Invocation-{} Status QUEUED - ".format(num_inv),

                "^job: 'jenkinsflow_test__multiple_invocations_parallel_same_flow_no_args_singlequeued__j1' Invocation-1 stopped running",
                "^job: 'jenkinsflow_test__multiple_invocations_parallel_same_flow_no_args_singlequeued__j1' Invocation-1 Status IDLE - build: #",
                "^SUCCESS: 'jenkinsflow_test__multiple_invocations_parallel_same_flow_no_args_singlequeued__j1' Invocation-1",

                build_started_msg(api, "jenkinsflow_test__multiple_invocations_parallel_same_flow_no_args_singlequeued__j1", 2, invocation_number=num_inv),
                "^job: 'jenkinsflow_test__multiple_invocations_parallel_same_flow_no_args_singlequeued__j1' Invocation-{} stopped running".format(num_inv),
                "^job: 'jenkinsflow_test__multiple_invocations_parallel_same_flow_no_args_singlequeued__j1' Invocation-{} Status IDLE - build: #".format(num_inv),
                "^SUCCESS: 'jenkinsflow_test__multiple_invocations_parallel_same_flow_no_args_singlequeued__j1' Invocation-{}".format(num_inv),
            ),
            "^parallel flow: (",
            "job: 'jenkinsflow_test__multiple_invocations_parallel_same_flow_no_args_singlequeued__j1' Invocation-1 SUCCESS",
            # python3 TODO: *[any_superseeded for _ in range(0, num_inv)]
            any_superseeded,
            any_superseeded,
            any_superseeded,
            "job: 'jenkinsflow_test__multiple_invocations_parallel_same_flow_no_args_singlequeued__j1' Invocation-{} SUCCESS".format(num_inv),
            "^)",
        )

        # Make sure that first and last are SUCCESS
        re.match("parallel flow: \\(\n *job: 'jenkinsflow_test__multiple_invocations_parallel_same_flow_no_args_singlequeued__j1' SUCCESS", sout)
        re.match("job: 'jenkinsflow_test__multiple_invocations_parallel_same_flow_no_args_singlequeued__j1' SUCCESS\n *\\)", sout)


def test_multiple_invocations_parallel_same_flow_running(api_type, capsys):
    """Requires job to be setup allowing simultaneous executions"""
    xfail("TODO Note: Test job allowing concurrent builds!")
