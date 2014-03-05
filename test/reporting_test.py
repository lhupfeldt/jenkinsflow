# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from jenkinsflow.flow import serial, _hyperspeed_speedup
from framework import mock_api


def test_reporting_job_status(capsys):
    with mock_api.api(__file__) as api:
        api.flow_job()
        api.job('j11', 0.1, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j12', 1.5, max_fails=0, expect_invocations=1, invocation_delay=1.0, initial_buildno=7, expect_order=2)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=0.5/_hyperspeed_speedup) as ctrl1:
            ctrl1.invoke('j11')
            ctrl1.invoke('j12')

        sout, _ = capsys.readouterr()
        repr_not_invoked = "job: 'jenkinsflow_test__reporting_job_status__j11' Status IDLE - latest build: None"
        assert repr_not_invoked in sout, repr_not_invoked + "\n - NOT FOUND IN:\n" + sout

        if api.is_mocked:
            assert "job: 'jenkinsflow_test__reporting_job_status__j12' Status IDLE - latest build: #7" in sout
            assert "'jenkinsflow_test__reporting_job_status__j12' Status QUEUED - latest build: #7" in sout
            assert "'jenkinsflow_test__reporting_job_status__j12' Status RUNNING - latest build: #8" in sout
            assert "'jenkinsflow_test__reporting_job_status__j12' Status IDLE - latest build: #8" in sout
        else:
            assert "'jenkinsflow_test__reporting_job_status__j12' Status RUNNING - latest build: #1" in sout
            assert "'jenkinsflow_test__reporting_job_status__j12' Status IDLE - latest build: #1" in sout
