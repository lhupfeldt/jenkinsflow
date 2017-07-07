# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import re
from pytest import raises

from jenkinsflow.flow import serial, parallel, FailedChildJobException
from .cfg import ApiType
from .framework import api_select
from .framework.utils import lines_in, replace_host_port, result_msg, build_started_msg


def test_reporting_job_status(api_type, capsys):
    with api_select.api(__file__, api_type) as api:
        api.flow_job()
        api.job('j11', max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j12', max_fails=0, expect_invocations=1, invocation_delay=1.0, exec_time=1.5, initial_buildno=7, expect_order=2, serial=True)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=0.5/api.speedup) as ctrl1:
            ctrl1.invoke('j11')
            ctrl1.invoke('j12')

        sout, _ = capsys.readouterr()

        if api.api_type == ApiType.MOCK:
            repr_not_invoked = "job: 'jenkinsflow_test__reporting_job_status__j11' Status IDLE - latest build: "
            assert repr_not_invoked in sout, repr_not_invoked + "\n - NOT FOUND IN:\n" + sout
            assert lines_in(api_type, sout, "job: 'jenkinsflow_test__reporting_job_status__j12' Status IDLE - latest build: #7")
            assert lines_in(api_type, sout, "'jenkinsflow_test__reporting_job_status__j12' Status QUEUED - Why am I queued?")
            assert lines_in(api_type, sout, "'jenkinsflow_test__reporting_job_status__j12' Status RUNNING - build: #8")
            assert lines_in(api_type, sout, "'jenkinsflow_test__reporting_job_status__j12' Status IDLE - build: #8")
        else:
            # TODO: know if we cleaned jobs and check the 'repr_not_invoked' above
            assert "'jenkinsflow_test__reporting_job_status__j12' Status RUNNING - build: " in sout
            # assert "'jenkinsflow_test__reporting_job_status__j12' Status IDLE - build: " in sout


def test_reporting_invocation_serial(api_type, capsys):
    with api_select.api(__file__, api_type) as api:
        api.flow_job()
        api.job('j11', max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j12', max_fails=0, expect_invocations=1, invocation_delay=1.0, exec_time=1.5, initial_buildno=7, expect_order=2, serial=True)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=0.5/api.speedup) as ctrl1:
            ctrl1.invoke('j11')
            ctrl1.invoke('j12')

        sout, _ = capsys.readouterr()
        empty_re = re.compile("^$")
        assert lines_in(
            api_type, sout,
            "^Defined Invocation http://x.x/job/jenkinsflow_test__reporting_invocation_serial__j11",
            "^Defined Invocation http://x.x/job/jenkinsflow_test__reporting_invocation_serial__j12",
            empty_re,
            "--- Starting flow ---",
            empty_re,
            "^Flow Invocation (1/1,1/1): ['jenkinsflow_test__reporting_invocation_serial__j11', 'jenkinsflow_test__reporting_invocation_serial__j12']",
            "^Job Invocation (1/1,1/1): http://x.x/job/jenkinsflow_test__reporting_invocation_serial__j11",
            build_started_msg(api, "jenkinsflow_test__reporting_invocation_serial__j11", 1),
            "^Job Invocation (1/1,1/1): http://x.x/job/jenkinsflow_test__reporting_invocation_serial__j12",
            build_started_msg(api, "jenkinsflow_test__reporting_invocation_serial__j12", 8),
        )


def test_reporting_invocation_parallel(api_type, capsys):
    with api_select.api(__file__, api_type) as api:
        api.flow_job()
        api.job('j11', max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j12', max_fails=0, expect_invocations=1, invocation_delay=1.0, exec_time=1.5, initial_buildno=7, expect_order=2)

        with parallel(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=0.5/api.speedup) as ctrl1:
            ctrl1.invoke('j11')
            ctrl1.invoke('j12')

        sout, _ = capsys.readouterr()
        assert lines_in(
            api_type, sout,
            "^Flow Invocation (1/1,1/1): ('jenkinsflow_test__reporting_invocation_parallel__j11', 'jenkinsflow_test__reporting_invocation_parallel__j12')",
            "^Job Invocation (1/1,1/1): http://x.x/job/jenkinsflow_test__reporting_invocation_parallel__j11",
            "^Job Invocation (1/1,1/1): http://x.x/job/jenkinsflow_test__reporting_invocation_parallel__j12",
        )

        assert lines_in(
            api_type, sout,
            "^Job Invocation (1/1,1/1): http://x.x/job/jenkinsflow_test__reporting_invocation_parallel__j11",
            build_started_msg(api, "jenkinsflow_test__reporting_invocation_parallel__j11", 1),
        )

        assert lines_in(
            api_type, sout,
            "^Job Invocation (1/1,1/1): http://x.x/job/jenkinsflow_test__reporting_invocation_parallel__j12",
            build_started_msg(api, "jenkinsflow_test__reporting_invocation_parallel__j12", 8)
        )


def test_reporting_multiple_invocations(api_type, capsys):
    with api_select.api(__file__, api_type) as api:
        api.flow_job()
        api.job('j11', max_fails=0, expect_invocations=3, expect_order=None)
        api.job('j12', max_fails=0, expect_invocations=1, invocation_delay=1.0, exec_time=1.5, initial_buildno=7, expect_order=4, serial=True)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=0.5/api.speedup) as ctrl1:
            ctrl1.invoke('j11')
            ctrl1.invoke('j11')
            ctrl1.invoke('j11')
            ctrl1.invoke('j12')

        sout, _ = capsys.readouterr()
        empty_re = re.compile("^$")
        assert lines_in(
            api_type, sout,
            "^Defined Invocation-1 http://x.x/job/jenkinsflow_test__reporting_multiple_invocations__j11",
            "^Defined Invocation-2 http://x.x/job/jenkinsflow_test__reporting_multiple_invocations__j11",
            "^Defined Invocation-3 http://x.x/job/jenkinsflow_test__reporting_multiple_invocations__j11",
            "^Defined Invocation http://x.x/job/jenkinsflow_test__reporting_multiple_invocations__j12",
            empty_re,
            "--- Starting flow ---",
            empty_re,
            "^Flow Invocation (1/1,1/1): ['jenkinsflow_test__reporting_multiple_invocations__j11', 'jenkinsflow_test__reporting_multiple_invocations__j11', 'jenkinsflow_test__reporting_multiple_invocations__j11', 'jenkinsflow_test__reporting_multiple_invocations__j12']",
            "^Job Invocation-1 (1/1,1/1): http://x.x/job/jenkinsflow_test__reporting_multiple_invocations__j11",
            build_started_msg(api, "jenkinsflow_test__reporting_multiple_invocations__j11", 1, invocation_number=1),
            "^Job Invocation (1/1,1/1): http://x.x/job/jenkinsflow_test__reporting_multiple_invocations__j12",
            build_started_msg(api, "jenkinsflow_test__reporting_multiple_invocations__j12", 8),
        )


def test_reporting_retry(api_type, capsys):
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

        sout, _ = capsys.readouterr()
        outer_flow_repr = "['jenkinsflow_test__reporting_retry__j11_fail', 'jenkinsflow_test__reporting_retry__j12', " \
                          "('jenkinsflow_test__reporting_retry__j21', 'jenkinsflow_test__reporting_retry__j22_fail', " \
                          "['jenkinsflow_test__reporting_retry__j31_fail', 'jenkinsflow_test__reporting_retry__j32'], " \
                          "'jenkinsflow_test__reporting_retry__j23'), 'jenkinsflow_test__reporting_retry__j13']"
        assert lines_in(
            api_type, sout,
            "^Flow Invocation (1/2,1/2): " + outer_flow_repr,
            "^Job Invocation (1/2,1/2): http://x.x/job/jenkinsflow_test__reporting_retry__j11_fail",
            build_started_msg(api, "jenkinsflow_test__reporting_retry__j11_fail", 1),
            "^FAILURE: 'jenkinsflow_test__reporting_retry__j11_fail'",
            "^RETRY: job: 'jenkinsflow_test__reporting_retry__j11_fail' failed, retrying child jobs from beginning. Up to 1 more times in current flow",
            "^Job Invocation (2/2,2/2): http://x.x/job/jenkinsflow_test__reporting_retry__j11_fail",
            build_started_msg(api, "jenkinsflow_test__reporting_retry__j11_fail", 2),
            "^SUCCESS: 'jenkinsflow_test__reporting_retry__j11_fail'",
            "^Job Invocation (1/3,1/6): http://x.x/job/jenkinsflow_test__reporting_retry__j23",
            build_started_msg(api, "jenkinsflow_test__reporting_retry__j23", 1),
            "^SUCCESS: 'jenkinsflow_test__reporting_retry__j23'",
            "^Job Invocation (1/2,1/2): http://.x.x/job/jenkinsflow_test__reporting_retry__j13",
            build_started_msg(api, "jenkinsflow_test__reporting_retry__j13", 1),
            "^Flow SUCCESS " + outer_flow_repr
        )

        assert lines_in(
            api_type, sout,
            "^Job Invocation (1/2,1/12): http://x.x/job/jenkinsflow_test__reporting_retry__j31_fail",
            build_started_msg(api, "jenkinsflow_test__reporting_retry__j31_fail", 1),
            "^FAILURE: 'jenkinsflow_test__reporting_retry__j31_fail'",
            "^RETRY: job: 'jenkinsflow_test__reporting_retry__j31_fail' failed, retrying child jobs from beginning. Up to 1 more times in current flow",
            "^Job Invocation (2/2,2/12): http://.x.x/job/jenkinsflow_test__reporting_retry__j31_fail",
            build_started_msg(api, "jenkinsflow_test__reporting_retry__j31_fail", 2),
            "^FAILURE: 'jenkinsflow_test__reporting_retry__j31_fail'",
            "^RETRY: job: 'jenkinsflow_test__reporting_retry__j31_fail' failed, retrying child jobs from beginning. Up to 10 more times through outer flow",
            "^Job Invocation (1/2,3/12): http://x.x/job/jenkinsflow_test__reporting_retry__j31_fail",
            build_started_msg(api, "jenkinsflow_test__reporting_retry__j31_fail", 3),
            "^FAILURE: 'jenkinsflow_test__reporting_retry__j31_fail'",
            "^RETRY: job: 'jenkinsflow_test__reporting_retry__j31_fail' failed, retrying child jobs from beginning. Up to 1 more times in current flow",
            "^Job Invocation (2/2,4/12): http://x.x/job/jenkinsflow_test__reporting_retry__j31_fail",
            build_started_msg(api, "jenkinsflow_test__reporting_retry__j31_fail", 4),
            "^SUCCESS: 'jenkinsflow_test__reporting_retry__j31_fail'"
        )


def test_reporting_result_unchecked(api_type, capsys):
    with api_select.api(__file__, api_type, login=True) as api:
        api.flow_job()
        api.job('j11', max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j21_unchecked', max_fails=0, expect_invocations=1, invocation_delay=0, exec_time=50, initial_buildno=7, expect_order=None, unknown_result=True, serial=True)
        api.job('j22', max_fails=0, expect_invocations=1, invocation_delay=0, exec_time=1.5, initial_buildno=7, expect_order=2)
        api.job('j31', max_fails=0, expect_invocations=1, invocation_delay=0, exec_time=1.5, initial_buildno=7, expect_order=3)
        api.job('j32_unchecked_fail', max_fails=1, expect_invocations=1, invocation_delay=0, exec_time=1.5, initial_buildno=7, expect_order=3)
        api.job('j41', max_fails=0, expect_invocations=1, invocation_delay=0, exec_time=1.5, initial_buildno=7, expect_order=3)
        api.job('j42_unchecked', max_fails=0, expect_invocations=1, invocation_delay=0, exec_time=1.5, initial_buildno=7, expect_order=3, serial=True)
        api.job('j23', max_fails=0, expect_invocations=1, invocation_delay=0, exec_time=1.5, initial_buildno=7, expect_order=4)
        api.job('j12', max_fails=0, expect_invocations=1, invocation_delay=0, exec_time=5, initial_buildno=7, expect_order=5)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=0.5/api.speedup) as ctrl1:
            ctrl1.invoke('j11')
            with ctrl1.serial() as ctrl2:
                ctrl2.invoke_unchecked('j21_unchecked')
                ctrl2.invoke('j22')
                with ctrl2.parallel() as ctrl3:
                    ctrl3.invoke('j31')
                    ctrl3.invoke_unchecked('j32_unchecked_fail')
                    with ctrl3.serial() as ctrl4:
                        ctrl4.invoke('j41')
                        ctrl4.invoke_unchecked('j42_unchecked')
                ctrl2.invoke('j23')
            ctrl1.invoke('j12')

        sout, _ = capsys.readouterr()

        assert lines_in(
            api_type, sout,
            "^UNCHECKED FAILURE: " + result_msg(api, "jenkinsflow_test__reporting_result_unchecked__j32_unchecked_fail"),
            "^UNCHECKED SUCCESS: " + result_msg(api, "jenkinsflow_test__reporting_result_unchecked__j42_unchecked", 8),
        )

def test_reporting_defined_job_parameters(api_type, capsys):
    with api_select.api(__file__, api_type) as api:
        api.flow_job()
        api.job('j1', max_fails=0, expect_invocations=1, invocation_delay=1.0, exec_time=1.5, initial_buildno=7, expect_order=1, serial=True,
                params=(('s1', '', 'desc'), ('c1', 'what', 'desc'), ('i1', 1, 'integer'), ('b1', False, 'boolean')))

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=0.5/api.speedup) as ctrl1:
            ctrl1.invoke('j1', s1="hi", c1='why?', i1=2, b1=True)

        sout, _ = capsys.readouterr()
        assert lines_in(
            api_type, sout,
            "^Defined Invocation http://x.x/job/jenkinsflow_test__reporting_defined_job_parameters__j1 - parameters:",
            "    i1 = '2'",
        )

        assert "    s1 = 'hi'" in sout
        assert "    c1 = 'why?'" in sout
        assert "    b1 = 'true'" in sout


ordered_params_output = """
Defined Invocation http://x.x/job/jenkinsflow_test__reporting_ordered_job_parameters__j1 - parameters:
     s1 = 'hi'
     s2 = 'not-last'
     c1 = 'why?'
     i1 = '2'
     b1 = 'true'
     s4 = 'was last'
     aaa = '3'
     unknown1 = 'Hello'
     unknown2 = 'true'
     s3 = 'last'
"""

def test_reporting_ordered_job_parameters(api_type, capsys):
    with api_select.api(__file__, api_type) as api:
        api.flow_job()
        api.job('j1', max_fails=0, expect_invocations=1, invocation_delay=1.0, exec_time=1.5, initial_buildno=7, expect_order=1, serial=True,
                params=(('s1', '', 'desc'), ('c1', 'what', 'desc'), ('i1', 1, 'integer'), ('b1', False, 'boolean'), ('s2', 't', 'd'), ('s3', 't2', 'd2'),
                        ('unknown1', 'Hello', 'd'), ('aaa', 17, 'd'), ('unknown2', False, 'd')))

        order = ['s1', 's2', 'c1', 'i1', 'b1', 's4', '*', 's3']
        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=0.5/api.speedup, params_display_order=order) as ctrl1:
            ctrl1.invoke('j1', s1="hi", c1='why?', i1=2, b1=True, s2='not-last', s3='last', unknown1='Hello', aaa=3, unknown2=True, s4='was last')

        sout, _ = capsys.readouterr()
        assert replace_host_port(api_type, ordered_params_output.strip()) in replace_host_port(api_type, sout)


def test_reporting_defined_non_existing(api_type, capsys):
    with api_select.api(__file__, api_type) as api:
        api.flow_job()
        # TODO
        with raises(FailedChildJobException):
            with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=0.5/api.speedup, allow_missing_jobs=True) as ctrl1:
                ctrl1.invoke('j1', a="b", c='d')

        sout, _ = capsys.readouterr()
        assert lines_in(
            api_type, sout,
            "Defined Invocation 'jenkinsflow_test__reporting_defined_non_existing__j1' - MISSING JOB",
            "    a = 'b'",
        )
        assert "    c = 'd'" in sout
