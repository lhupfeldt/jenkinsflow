# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from pytest import raises

from jenkinsflow.flow import parallel, serial, MissingJobsException, FailedChildJobsException, FailedChildJobException
from .framework import api_select


def test_missing_jobs_not_allowed():
    with api_select.api(__file__) as api:
        api.flow_job()
        api.job('j1', 0.01, max_fails=0, expect_invocations=0, expect_order=None)
        api.job('j2', 0.01, max_fails=0, expect_invocations=0, expect_order=None)

        with raises(MissingJobsException) as exinfo:
            with serial(api, 20, job_name_prefix=api.job_name_prefix) as ctrl1:
                ctrl1.invoke('j1')
                ctrl1.invoke('missingA')
                ctrl1.invoke('j2')

        print exinfo.value
        assert "Job not found: jenkinsflow_test__missing_jobs_not_allowed__missingA" in exinfo.value.message

        with raises(MissingJobsException):
            with serial(api, 20, job_name_prefix=api.job_name_prefix) as ctrl1:
                ctrl1.invoke('j1')
                ctrl1.invoke('missingA')
                with ctrl1.parallel() as ctrl2:
                    ctrl2.invoke('missingB')
                    ctrl2.invoke('j2')
                ctrl1.invoke('missingC')


def test_missing_jobs_allowed_still_missing_parallel():
    with api_select.api(__file__) as api:
        api.flow_job()
        api.job('j1', 0.01, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j2', 0.01, max_fails=0, expect_invocations=1, expect_order=1)

        with raises(FailedChildJobsException):
            with parallel(api, 20, job_name_prefix=api.job_name_prefix, allow_missing_jobs=True) as ctrl1:
                ctrl1.invoke('j1')
                ctrl1.invoke('missingA')
                ctrl1.invoke('j2')


def test_missing_jobs_allowed_still_missing_serial():
    with api_select.api(__file__) as api:
        api.flow_job()
        api.job('j1', 0.01, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j2', 0.01, max_fails=0, expect_invocations=0, expect_order=None)

        with raises(FailedChildJobException):
            with serial(api, 20, job_name_prefix=api.job_name_prefix, allow_missing_jobs=True) as ctrl1:
                ctrl1.invoke('j1')
                ctrl1.invoke('missingA')
                ctrl1.invoke('j2')


def test_missing_jobs_allowed_still_missing_parallel_serial():
    with api_select.api(__file__) as api:
        api.flow_job()
        api.job('j1', 0.01, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j2', 0.01, max_fails=0, expect_invocations=0, expect_order=None)

        with raises(FailedChildJobsException):
            with parallel(api, 20, job_name_prefix=api.job_name_prefix, allow_missing_jobs=True) as ctrl1:
                ctrl1.invoke('j1')
                ctrl1.invoke('missingA')
                with ctrl1.serial() as ctrl2:
                    ctrl2.invoke('missingB')
                    ctrl2.invoke('j2')
                ctrl1.invoke('missingC')


# TODO Jobs created during flow!
