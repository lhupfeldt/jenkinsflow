# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from jenkinsflow.flow import serial, parallel
from .cfg import ApiType
from .framework import api_select
from .framework.utils import assert_lines_in, build_started_msg


def test_multiple_invocations_same_flow():
    with api_select.api(__file__) as api:
        api.flow_job()
        _params = (('password', '', 'Some password'), ('s1', '', 'Some string argument'))
        api.job('j1', exec_time=0.01, max_fails=0, expect_invocations=2, expect_order=1, params=_params)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=1) as ctrl1:
            ctrl1.invoke('j1', password='a', s1='b')
            ctrl1.invoke('j1', password='something else', s1='asdasdasdasdad')


def test_multiple_invocations_same_flow_same_args():
    with api_select.api(__file__) as api:
        api.flow_job()
        _params = (('password', '', 'Some password'), ('s1', '', 'Some string argument'))
        api.job('j1', exec_time=0.01, max_fails=0, expect_invocations=2, expect_order=1, params=_params)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=1) as ctrl1:
            ctrl1.invoke('j1', password='a', s1='b')
            ctrl1.invoke('j1', password='a', s1='b')


def test_multiple_invocations_new_flow():
    with api_select.api(__file__) as api:
        api.flow_job()
        _params = (('password', '', 'Some password'), ('s1', '', 'Some string argument'))
        api.job('j1', exec_time=0.01, max_fails=0, expect_invocations=2, expect_order=1, params=_params)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=1) as ctrl1:
            ctrl1.invoke('j1', password='a', s1='b')

        with serial(api, timeout=15, job_name_prefix=api.job_name_prefix, report_interval=1) as ctrl1:
            ctrl1.invoke('j1', password='something else', s1='asdasdasdasdad')


def test_multiple_invocations_new_flow_same_args():
    with api_select.api(__file__) as api:
        api.flow_job()
        _params = (('password', '', 'Some password'), ('s1', '', 'Some string argument'))
        api.job('j1', exec_time=0.01, max_fails=0, expect_invocations=2, expect_order=1, params=_params)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=1) as ctrl1:
            ctrl1.invoke('j1', password='a', s1='b')

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=1) as ctrl1:
            ctrl1.invoke('j1', password='a', s1='b')


def test_multiple_invocations_same_flow_queued(capsys):
    with api_select.api(__file__) as api:
        if api.api_type in (ApiType.MOCK, ApiType.SCRIPT):
            # TODO
            return

        api.flow_job()
        _params = (('password', '', 'Some password'), ('s1', '', 'Some string argument'))
        api.job('j1', exec_time=3, max_fails=0, expect_invocations=3, expect_order=1, params=_params)

        with parallel(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=1) as ctrl1:
            ctrl1.invoke('j1', password='a', s1='invocation1')
            ctrl1.invoke('j1', password='b', s1='invocation2')
            ctrl1.invoke('j1', password='b', s1='invocation3')

        # Note: This output order depends on the job NOT allowing concurrent builds, AND on the order of polling in jenkins_api!
        if api.api_type != ApiType.MOCK:
            sout, _ = capsys.readouterr()
            assert_lines_in(
                sout,
                "^Invoking Job (1/1,1/1): http://x.x/job/jenkinsflow_test__multiple_invocations_same_flow_queued__j1",
                "^Invoking Job (1/1,1/1): http://x.x/job/jenkinsflow_test__multiple_invocations_same_flow_queued__j1",
                "^Invoking Job (1/1,1/1): http://x.x/job/jenkinsflow_test__multiple_invocations_same_flow_queued__j1",

                build_started_msg(api, "jenkinsflow_test__multiple_invocations_same_flow_queued__j1", 1),
                "^job: 'jenkinsflow_test__multiple_invocations_same_flow_queued__j1' stopped running",
                "^job: 'jenkinsflow_test__multiple_invocations_same_flow_queued__j1' Status IDLE - build: #",
                "^SUCCESS: 'jenkinsflow_test__multiple_invocations_same_flow_queued__j1'",

                build_started_msg(api, "jenkinsflow_test__multiple_invocations_same_flow_queued__j1", 2),
                "^job: 'jenkinsflow_test__multiple_invocations_same_flow_queued__j1' stopped running",
                "^job: 'jenkinsflow_test__multiple_invocations_same_flow_queued__j1' Status IDLE - build: #",
                "^SUCCESS: 'jenkinsflow_test__multiple_invocations_same_flow_queued__j1'",

                build_started_msg(api, "jenkinsflow_test__multiple_invocations_same_flow_queued__j1", 3),
                "^job: 'jenkinsflow_test__multiple_invocations_same_flow_queued__j1' stopped running",
                "^job: 'jenkinsflow_test__multiple_invocations_same_flow_queued__j1' Status IDLE - build: #",
                "^SUCCESS: 'jenkinsflow_test__multiple_invocations_same_flow_queued__j1'",

                "^parallel flow: (",
                "job: 'jenkinsflow_test__multiple_invocations_same_flow_queued__j1' SUCCESS",
                "job: 'jenkinsflow_test__multiple_invocations_same_flow_queued__j1' SUCCESS",
                "job: 'jenkinsflow_test__multiple_invocations_same_flow_queued__j1' SUCCESS", 
                "^)",
            )
