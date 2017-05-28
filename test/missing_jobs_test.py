# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import re

import pytest
from pytest import raises

from jenkinsflow.flow import parallel, serial, MissingJobsException, FailedChildJobsException, FailedChildJobException, UnknownJobException
from .framework import api_select
from .framework.utils import lines_in
from .cfg import ApiType


def test_missing_jobs_not_allowed(api_type):
    with api_select.api(__file__, api_type) as api:
        api.flow_job()
        api.job('j1', max_fails=0, expect_invocations=0, expect_order=None)
        api.job('j2', max_fails=0, expect_invocations=0, expect_order=None)

        with raises(MissingJobsException) as exinfo:
            with serial(api, 20, job_name_prefix=api.job_name_prefix) as ctrl1:
                ctrl1.invoke('j1')
                ctrl1.invoke('missingA')
                ctrl1.invoke('j2')

        assert lines_in(
            api_type, str(exinfo.value),
            re.compile("^Job not found: .*jenkinsflow_test__missing_jobs_not_allowed__missingA")
        )

        with raises(MissingJobsException):
            with serial(api, 20, job_name_prefix=api.job_name_prefix) as ctrl1:
                ctrl1.invoke('j1')
                ctrl1.invoke('missingA')
                with ctrl1.parallel() as ctrl2:
                    ctrl2.invoke('missingB')
                    ctrl2.invoke('j2')
                ctrl1.invoke('missingC')


def test_missing_jobs_allowed_still_missing_parallel(api_type):
    with api_select.api(__file__, api_type) as api:
        api.flow_job()
        api.job('j1', max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j2', max_fails=0, expect_invocations=1, expect_order=1)

        with raises(FailedChildJobsException):
            with parallel(api, 20, job_name_prefix=api.job_name_prefix, allow_missing_jobs=True) as ctrl1:
                ctrl1.invoke('j1')
                ctrl1.invoke('missingA')
                ctrl1.invoke('j2')


def test_missing_jobs_allowed_still_missing_serial(api_type):
    with api_select.api(__file__, api_type) as api:
        api.flow_job()
        api.job('j1', max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j2', max_fails=0, expect_invocations=0, expect_order=None)

        with raises(FailedChildJobException):
            with serial(api, 20, job_name_prefix=api.job_name_prefix, allow_missing_jobs=True) as ctrl1:
                ctrl1.invoke('j1')
                ctrl1.invoke('missingA')
                ctrl1.invoke('j2')


def test_missing_jobs_allowed_still_missing_parallel_serial(api_type):
    with api_select.api(__file__, api_type) as api:
        api.flow_job()
        api.job('j1', max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j2', max_fails=0, expect_invocations=0, expect_order=None)

        with raises(FailedChildJobsException):
            with parallel(api, 20, job_name_prefix=api.job_name_prefix, allow_missing_jobs=True) as ctrl1:
                ctrl1.invoke('j1')
                ctrl1.invoke('missingA')
                with ctrl1.serial() as ctrl2:
                    ctrl2.invoke('missingB')
                    ctrl2.invoke('j2')
                ctrl1.invoke('missingC')


@pytest.mark.not_apis(ApiType.SCRIPT)  # TODO: Handle ApiType.SCRIPT
def test_missing_jobs_allowed_created_serial_parallel(api_type):
    with api_select.api(__file__, api_type) as api:
        with api.job_creator():
            api.flow_job()
            api.job('j1', max_fails=0, expect_invocations=1, expect_order=1, create_job='missingA')
            api.job('missingA', max_fails=0, expect_invocations=1, expect_order=2, flow_created=True, create_job='missingB')
            api.job('missingB', max_fails=0, expect_invocations=1, expect_order=3, flow_created=True)
            api.job('j2', max_fails=0, expect_invocations=1, expect_order=3, create_job='missingC')
            api.job('missingC', max_fails=0, expect_invocations=1, expect_order=4, flow_created=True)

        with serial(api, 20, job_name_prefix=api.job_name_prefix, allow_missing_jobs=True) as ctrl1:
            ctrl1.invoke('j1')
            ctrl1.invoke('missingA')
            with ctrl1.parallel() as ctrl2:
                ctrl2.invoke('missingB')
                ctrl2.invoke('j2')
            ctrl1.invoke('missingC')

        # TODO: Validate output


@pytest.mark.not_apis(ApiType.MOCK, ApiType.SCRIPT)  # TODO: Handle ApiTypes
def test_missing_jobs_job_disappeared(api_type):
    with api_select.api(__file__, api_type) as api:
        with api.job_creator():
            api.flow_job()
            api.job('j1', max_fails=0, expect_invocations=1, expect_order=1)
            api.job('disappearing', max_fails=0, expect_invocations=0, expect_order=None, disappearing=True)

        with raises(UnknownJobException):
            with serial(api, 20, job_name_prefix=api.job_name_prefix, allow_missing_jobs=True) as ctrl1:
                ctrl1.invoke('j1')
                ctrl1.invoke('disappearing')

        # TODO: Validate output
