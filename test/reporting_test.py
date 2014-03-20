# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from jenkinsflow.flow import serial, parallel, _hyperspeed_speedup
from .framework import mock_api
from .framework.utils import assert_lines_in


def test_reporting_job_status(capsys):
    with mock_api.api(__file__) as api:
        api.flow_job()
        api.job('j11', 0.1, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j12', 1.5, max_fails=0, expect_invocations=1, invocation_delay=1.0, initial_buildno=7, expect_order=2, serial=True)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=0.5/_hyperspeed_speedup) as ctrl1:
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

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=0.5/_hyperspeed_speedup) as ctrl1:
            ctrl1.invoke('j11')
            ctrl1.invoke('j12')

        sout, _ = capsys.readouterr()
        assert_lines_in(
            sout,
            "Invoking Flow (1/1,1/1): ['jenkinsflow_test__reporting_invocation_serial__j11', 'jenkinsflow_test__reporting_invocation_serial__j12']",
            "Invoking Job (1/1,1/1): http://x.x/job/jenkinsflow_test__reporting_invocation_serial__j11 - /build",
            "Invoking Job (1/1,1/1): http://x.x/job/jenkinsflow_test__reporting_invocation_serial__j12 - /build"
        )


def test_reporting_invocation_parallel(capsys):
    with mock_api.api(__file__) as api:
        api.flow_job()
        api.job('j11', 0.1, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j12', 1.5, max_fails=0, expect_invocations=1, invocation_delay=1.0, initial_buildno=7, expect_order=2)

        with parallel(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=0.5/_hyperspeed_speedup) as ctrl1:
            ctrl1.invoke('j11')
            ctrl1.invoke('j12')

        sout, _ = capsys.readouterr()
        assert_lines_in(
            sout,
            "Invoking Flow (1/1,1/1): ('jenkinsflow_test__reporting_invocation_parallel__j11', 'jenkinsflow_test__reporting_invocation_parallel__j12')",
            "Invoking Job (1/1,1/1): http://x.x/job/jenkinsflow_test__reporting_invocation_parallel__j11 - /build",
            "Invoking Job (1/1,1/1): http://x.x/job/jenkinsflow_test__reporting_invocation_parallel__j12 - /build"
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
            "Invoking Flow (1/2,1/2): " + outer_flow_repr,
            "Invoking Job (1/2,1/2): http://x.x/job/jenkinsflow_test__reporting_retry__j11_fail - /buildWithParameters",
            "FAILURE: 'jenkinsflow_test__reporting_retry__j11_fail'",
            "RETRY: http://x.x/job/jenkinsflow_test__reporting_retry__j11_fail - /buildWithParameters failed, retrying child jobs from beginning. Up to 1 more times in current flow",
            "Invoking Job (2/2,2/2): http://x.x/job/jenkinsflow_test__reporting_retry__j11_fail",
            "SUCCESS: 'jenkinsflow_test__reporting_retry__j11_fail'",
            "Invoking Job (1/3,1/6): http://x.x/job/jenkinsflow_test__reporting_retry__j23",
            "SUCCESS: 'jenkinsflow_test__reporting_retry__j23'",
            "Invoking Job (1/2,1/2): http://x.x/job/jenkinsflow_test__reporting_retry__j13",
            "SUCCESS " + outer_flow_repr
        )

        assert_lines_in(
            sout,
            "Invoking Job (1/2,1/12): http://x.x/job/jenkinsflow_test__reporting_retry__j31_fail",
            "FAILURE: 'jenkinsflow_test__reporting_retry__j31_fail'",
            "RETRY: http://x.x/job/jenkinsflow_test__reporting_retry__j31_fail - /buildWithParameters failed, retrying child jobs from beginning. Up to 1 more times in current flow",
            "Invoking Job (2/2,2/12): http://x.x/job/jenkinsflow_test__reporting_retry__j31_fail",
            "FAILURE: 'jenkinsflow_test__reporting_retry__j31_fail'",
            "RETRY: http://x.x/job/jenkinsflow_test__reporting_retry__j31_fail - /buildWithParameters failed, retrying child jobs from beginning. Up to 10 more times through outer flow",
            "Invoking Job (1/2,3/12): http://x.x/job/jenkinsflow_test__reporting_retry__j31_fail",
            "FAILURE: 'jenkinsflow_test__reporting_retry__j31_fail'",
            "RETRY: http://x.x/job/jenkinsflow_test__reporting_retry__j31_fail - /buildWithParameters failed, retrying child jobs from beginning. Up to 1 more times in current flow",
            "Invoking Job (2/2,4/12): http://x.x/job/jenkinsflow_test__reporting_retry__j31_fail",
            "SUCCESS: 'jenkinsflow_test__reporting_retry__j31_fail'"
        )

# TODO
def test_reporting_job_status_unchecked(capsys):
    with mock_api.api(__file__) as api:
        api.flow_job()
        api.job('j11', 0.1, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j21_unchecked', 50, max_fails=0, expect_invocations=1, invocation_delay=0.0001, initial_buildno=7, expect_order=None, unknown_result=True, serial=True)
        api.job('j22', 1.5, max_fails=0, expect_invocations=1, invocation_delay=0.0001, initial_buildno=7, expect_order=2)
        api.job('j31', 1.5, max_fails=0, expect_invocations=1, invocation_delay=0.0001, initial_buildno=7, expect_order=3)
        api.job('j32_unchecked', 1.5, max_fails=1, expect_invocations=1, invocation_delay=0.0001, initial_buildno=7, expect_order=3)
        api.job('j41', 1.5, max_fails=0, expect_invocations=1, invocation_delay=0.0001, initial_buildno=7, expect_order=3)
        api.job('j42_unchecked', 1.5, max_fails=0, expect_invocations=1, invocation_delay=0.0001, initial_buildno=7, expect_order=3, serial=True)
        api.job('j23', 1.5, max_fails=0, expect_invocations=1, invocation_delay=0.0001, initial_buildno=7, expect_order=4)
        api.job('j12', 5, max_fails=0, expect_invocations=1, invocation_delay=0.0001, initial_buildno=7, expect_order=5)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=0.5/_hyperspeed_speedup) as ctrl1:
            ctrl1.invoke('j11')
            with ctrl1.serial() as ctrl2:
                ctrl2.invoke_unchecked('j21_unchecked')
                ctrl2.invoke('j22')
                with ctrl2.parallel() as ctrl3:
                    ctrl3.invoke('j31')
                    ctrl3.invoke_unchecked('j32_unchecked')
                    with ctrl3.serial() as ctrl4:
                        ctrl4.invoke('j41')
                        ctrl4.invoke_unchecked('j42_unchecked')
                ctrl2.invoke('j23')
            ctrl1.invoke('j12')

        sout, _ = capsys.readouterr()

        #if api.is_mocked:
        #    repr_not_invoked = "job: 'jenkinsflow_test__reporting_job_status_unchecked__j11' Status IDLE - latest build: "
        #    assert repr_not_invoked in sout, repr_not_invoked + "\n - NOT FOUND IN:\n" + sout
        #    assert "job: 'jenkinsflow_test__reporting_job_status_unchecked__j12' Status IDLE - latest build: #7" in sout
        #    assert "'jenkinsflow_test__reporting_job_status_unchecked__j12' Status QUEUED - latest build: #7" in sout
        #    assert "'jenkinsflow_test__reporting_job_status_unchecked__j12' Status RUNNING - latest build: #8" in sout
        #    assert "'jenkinsflow_test__reporting_job_status_unchecked__j12' Status IDLE - latest build: #8" in sout
        #else:
        #    # TODO: know if we cleaned jobs and check the 'repr_not_invoked' above
        #    assert "'jenkinsflow_test__reporting_job_status_unchecked__j12' Status RUNNING - latest build: " in sout
        #    # assert "'jenkinsflow_test__reporting_job_status_unchecked__j12' Status IDLE - latest build: " in sout
