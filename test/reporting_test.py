# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import re
from pytest import raises

from jenkinsflow.flow import serial, parallel, FailedChildJobException
from jenkinsflow.mocked import HyperSpeed
from .framework import mock_api
from .framework.utils import assert_lines_in, replace_host_port

hyperspeed = HyperSpeed()


def num_console(num, api):
    return str(num) + "/console" if api.is_mocked else ""


def test_reporting_job_status(capsys):
    with mock_api.api(__file__) as api:
        api.flow_job()
        api.job('j11', 0.1, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j12', 1.5, max_fails=0, expect_invocations=1, invocation_delay=1.0, initial_buildno=7, expect_order=2, serial=True)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=0.5/hyperspeed.speedup) as ctrl1:
            ctrl1.invoke('j11')
            ctrl1.invoke('j12')

        sout, _ = capsys.readouterr()

        if api.is_mocked:
            repr_not_invoked = "job: 'jenkinsflow_test__reporting_job_status__j11' Status IDLE - latest build: "
            assert repr_not_invoked in sout, repr_not_invoked + "\n - NOT FOUND IN:\n" + sout
            assert "job: 'jenkinsflow_test__reporting_job_status__j12' Status IDLE - latest build: #7" in sout
            assert "'jenkinsflow_test__reporting_job_status__j12' Status QUEUED - latest build: #7" in sout
            assert "'jenkinsflow_test__reporting_job_status__j12' Status RUNNING - latest build: #8" in sout
            assert "'jenkinsflow_test__reporting_job_status__j12' Status IDLE - latest build: #8" in sout
        else:
            # TODO: know if we cleaned jobs and check the 'repr_not_invoked' above
            assert "'jenkinsflow_test__reporting_job_status__j12' Status RUNNING - latest build: " in sout
            # assert "'jenkinsflow_test__reporting_job_status__j12' Status IDLE - latest build: " in sout


def test_reporting_invocation_serial(capsys):
    with mock_api.api(__file__) as api:
        api.flow_job()
        api.job('j11', 0.1, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j12', 1.5, max_fails=0, expect_invocations=1, invocation_delay=1.0, initial_buildno=7, expect_order=2, serial=True)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=0.5/hyperspeed.speedup) as ctrl1:
            ctrl1.invoke('j11')
            ctrl1.invoke('j12')

        sout, _ = capsys.readouterr()
        assert_lines_in(
            sout,
            "^Defined Job http://x.x/job/jenkinsflow_test__reporting_invocation_serial__j11",
            "^Defined Job http://x.x/job/jenkinsflow_test__reporting_invocation_serial__j12",
            re.compile("^$"),
            "--- Starting flow ---",
            re.compile("^$"),
            "^Invoking Flow (1/1,1/1): ['jenkinsflow_test__reporting_invocation_serial__j11', 'jenkinsflow_test__reporting_invocation_serial__j12']",
            "^Invoking Job (1/1,1/1): http://x.x/job/jenkinsflow_test__reporting_invocation_serial__j11/" + num_console(1, api),
            "^Invoking Job (1/1,1/1): http://x.x/job/jenkinsflow_test__reporting_invocation_serial__j12/" + num_console(8, api),
        )


def test_reporting_invocation_parallel(capsys):
    with mock_api.api(__file__) as api:
        api.flow_job()
        api.job('j11', 0.1, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j12', 1.5, max_fails=0, expect_invocations=1, invocation_delay=1.0, initial_buildno=7, expect_order=2)

        with parallel(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=0.5/hyperspeed.speedup) as ctrl1:
            ctrl1.invoke('j11')
            ctrl1.invoke('j12')

        sout, _ = capsys.readouterr()
        assert_lines_in(
            sout,
            "^Invoking Flow (1/1,1/1): ('jenkinsflow_test__reporting_invocation_parallel__j11', 'jenkinsflow_test__reporting_invocation_parallel__j12')",
            "^Invoking Job (1/1,1/1): http://x.x/job/jenkinsflow_test__reporting_invocation_parallel__j11/" + num_console(1, api),
            "^Invoking Job (1/1,1/1): http://x.x/job/jenkinsflow_test__reporting_invocation_parallel__j12/" + num_console(8, api)
        )


def test_reporting_retry(capsys):
    with mock_api.api(__file__) as api:
        api.flow_job()
        api.job('j11_fail', 0.01, max_fails=1, expect_invocations=2, expect_order=1)
        api.job('j12', 0.01, max_fails=0, expect_invocations=1, expect_order=2, serial=True)
        api.job('j21', 0.01, max_fails=0, expect_invocations=1, expect_order=3, serial=True)
        api.job('j22_fail', 0.01, max_fails=2, expect_invocations=3, expect_order=3)
        api.job('j31_fail', 0.01, max_fails=3, expect_invocations=4, expect_order=3)
        api.job('j32', 0.01, max_fails=0, expect_invocations=1, expect_order=3, serial=True)
        api.job('j23', 0.01, max_fails=0, expect_invocations=1, expect_order=3)
        api.job('j13', 0.01, max_fails=0, expect_invocations=1, expect_order=4, serial=True)

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
        assert_lines_in(
            sout,
            "^Invoking Flow (1/2,1/2): " + outer_flow_repr,
            "^Invoking Job (1/2,1/2): http://x.x/job/jenkinsflow_test__reporting_retry__j11_fail/" + num_console(1, api),
            "^FAILURE: 'jenkinsflow_test__reporting_retry__j11_fail'",
            "^RETRY: job: 'jenkinsflow_test__reporting_retry__j11_fail' failed, retrying child jobs from beginning. Up to 1 more times in current flow",
            "^Invoking Job (2/2,2/2): http://x.x/job/jenkinsflow_test__reporting_retry__j11_fail/" + num_console(2, api),
            "^SUCCESS: 'jenkinsflow_test__reporting_retry__j11_fail'",
            "^Invoking Job (1/3,1/6): http://x.x/job/jenkinsflow_test__reporting_retry__j23/" + num_console(1, api),
            "^SUCCESS: 'jenkinsflow_test__reporting_retry__j23'",
            "^Invoking Job (1/2,1/2): http://x.x/job/jenkinsflow_test__reporting_retry__j13/" + num_console(1, api),
            "^SUCCESS " + outer_flow_repr
        )

        assert_lines_in(
            sout,
            "^Invoking Job (1/2,1/12): http://x.x/job/jenkinsflow_test__reporting_retry__j31_fail/" + num_console(1, api),
            "^FAILURE: 'jenkinsflow_test__reporting_retry__j31_fail'",
            "^RETRY: job: 'jenkinsflow_test__reporting_retry__j31_fail' failed, retrying child jobs from beginning. Up to 1 more times in current flow",
            "^Invoking Job (2/2,2/12): http://x.x/job/jenkinsflow_test__reporting_retry__j31_fail/" + num_console(2, api),
            "^FAILURE: 'jenkinsflow_test__reporting_retry__j31_fail'",
            "^RETRY: job: 'jenkinsflow_test__reporting_retry__j31_fail' failed, retrying child jobs from beginning. Up to 10 more times through outer flow",
            "^Invoking Job (1/2,3/12): http://x.x/job/jenkinsflow_test__reporting_retry__j31_fail/" + num_console(3, api),
            "^FAILURE: 'jenkinsflow_test__reporting_retry__j31_fail'",
            "^RETRY: job: 'jenkinsflow_test__reporting_retry__j31_fail' failed, retrying child jobs from beginning. Up to 1 more times in current flow",
            "^Invoking Job (2/2,4/12): http://x.x/job/jenkinsflow_test__reporting_retry__j31_fail/" + num_console(4, api),
            "^SUCCESS: 'jenkinsflow_test__reporting_retry__j31_fail'"
        )


def test_reporting_result_unchecked(capsys):
    with mock_api.api(__file__) as api:
        api.flow_job()
        api.job('j11', 0.1, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j21_unchecked', 50, max_fails=0, expect_invocations=1, invocation_delay=0.0001, initial_buildno=7, expect_order=None, unknown_result=True, serial=True)
        api.job('j22', 1.5, max_fails=0, expect_invocations=1, invocation_delay=0.0001, initial_buildno=7, expect_order=2)
        api.job('j31', 1.5, max_fails=0, expect_invocations=1, invocation_delay=0.0001, initial_buildno=7, expect_order=3)
        api.job('j32_unchecked_fail', 1.5, max_fails=1, expect_invocations=1, invocation_delay=0.0001, initial_buildno=7, expect_order=3)
        api.job('j41', 1.5, max_fails=0, expect_invocations=1, invocation_delay=0.0001, initial_buildno=7, expect_order=3)
        api.job('j42_unchecked', 1.5, max_fails=0, expect_invocations=1, invocation_delay=0.0001, initial_buildno=7, expect_order=3, serial=True)
        api.job('j23', 1.5, max_fails=0, expect_invocations=1, invocation_delay=0.0001, initial_buildno=7, expect_order=4)
        api.job('j12', 5, max_fails=0, expect_invocations=1, invocation_delay=0.0001, initial_buildno=7, expect_order=5)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=0.5/hyperspeed.speedup) as ctrl1:
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

        assert_lines_in(
            sout,
            "^UNCHECKED FAILURE: 'jenkinsflow_test__reporting_result_unchecked__j32_unchecked_fail' - build: http://x.x/job/jenkinsflow_test__reporting_result_unchecked__j32_unchecked_fail/",
            "^UNCHECKED SUCCESS: 'jenkinsflow_test__reporting_result_unchecked__j42_unchecked' - build: http://x.x/job/jenkinsflow_test__reporting_result_unchecked__j42_unchecked/" + num_console(8, api)
        )

def test_reporting_defined_job_parameters(capsys):
    with mock_api.api(__file__) as api:
        api.flow_job()
        api.job('j1', 1.5, max_fails=0, expect_invocations=1, invocation_delay=1.0, initial_buildno=7, expect_order=1, serial=True,
                params=(('s1', '', 'desc'), ('c1', 'what', 'desc'), ('i1', 1, 'integer'), ('b1', False, 'boolean')))

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=0.5/hyperspeed.speedup) as ctrl1:
            ctrl1.invoke('j1', s1="hi", c1='why?', i1=2, b1=True)

        sout, _ = capsys.readouterr()
        assert_lines_in(
            sout,
            "^Defined Job http://x.x/job/jenkinsflow_test__reporting_defined_job_parameters__j1 - parameters:",
            "    i1 = '2'",
        )

        assert "    s1 = 'hi'" in sout
        assert "    c1 = 'why?'" in sout
        assert "    b1 = 'true'" in sout


ordered_params_output = """
Defined Job http://x.x/job/jenkinsflow_test__reporting_ordered_job_parameters__j1 - parameters:
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

def test_reporting_ordered_job_parameters(capsys):
    with mock_api.api(__file__) as api:
        api.flow_job()
        api.job('j1', 1.5, max_fails=0, expect_invocations=1, invocation_delay=1.0, initial_buildno=7, expect_order=1, serial=True,
                params=(('s1', '', 'desc'), ('c1', 'what', 'desc'), ('i1', 1, 'integer'), ('b1', False, 'boolean'), ('s2', 't', 'd'), ('s3', 't2', 'd2'),
                        ('unknown1', 'Hello', 'd'), ('aaa', 17, 'd'), ('unknown2', False, 'd')))

        order = ['s1', 's2', 'c1', 'i1', 'b1', 's4', '*', 's3']
        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=0.5/hyperspeed.speedup, params_display_order=order) as ctrl1:
            ctrl1.invoke('j1', s1="hi", c1='why?', i1=2, b1=True, s2='not-last', s3='last', unknown1='Hello', aaa=3, unknown2=True, s4='was last')

        sout, _ = capsys.readouterr()
        assert ordered_params_output.strip() in replace_host_port(sout)


def test_reporting_defined_non_existing(capsys):
    with mock_api.api(__file__) as api:
        api.flow_job()
        # TODO
        with raises(FailedChildJobException):
            with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=0.5/hyperspeed.speedup, allow_missing_jobs=True) as ctrl1:
                ctrl1.invoke('j1', a="b", c='d')

        sout, _ = capsys.readouterr()
        assert_lines_in(
            sout,
            "Defined Job 'jenkinsflow_test__reporting_defined_non_existing__j1' - MISSING JOB",
            "    a = 'b'",
        )
        assert "    c = 'd'" in sout
