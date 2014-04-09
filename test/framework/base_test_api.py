# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

import abc, os, time
from collections import OrderedDict

from .abstract_api import AbstractApiJob, AbstractApiBuild as TestBuild, AbstractApiJenkins

from jenkinsflow.flow import BuildResult, is_mocked


class TestJob(AbstractApiJob):
    __metaclass__ = abc.ABCMeta

    _current_order = 1

    def __init__(self, exec_time, max_fails, expect_invocations, expect_order, initial_buildno=None, invocation_delay=0.01, unknown_result=False, final_result=None, serial=False):
        """
        Set unknown_result to True if the result is indeterminate (timeout or invoke_unchecked)
        """
        assert exec_time > 0
        assert max_fails >= 0
        assert expect_invocations >= 0
        assert expect_order >= 1 or expect_order is None
        assert initial_buildno is None or initial_buildno >= 1
        assert invocation_delay > 0
        assert unknown_result in (False, True)
        assert serial in (False, True)

        self.exec_time = exec_time
        self.max_fails = max_fails
        self.expect_invocations = expect_invocations
        self.expect_order = expect_order
        self.initial_buildno = initial_buildno
        self.invocation_delay = invocation_delay
        self.unknown_result = unknown_result
        self.serial = serial
        self.final_result = final_result if isinstance(final_result, (BuildResult, type(None))) else BuildResult[final_result.upper()]

        self.invocation = 0
        self.invocation_time = self.start_time = self.end_time = 0
        self.actual_order = -1

        self.build_params = None

    @property
    def has_force_result_param(self):
        return self.max_fails > 0 or self.final_result

    def invoke(self, securitytoken=None, block=False, invoke_pre_check_delay=3, build_params=None, cause=None):
        self.build_params = build_params
        self.invocation += 1
        self.actual_order = TestJob._current_order
        TestJob._current_order += 1

    def __repr__(self):
        return ", expect_invocations: " + repr(self.expect_invocations) + \
            ", invocation: " + repr(self.invocation) + \
            ", expect_order: " + repr(self.expect_order) + \
            ", start_time: " + repr(self.start_time) + \
            ", exec_time: " + repr(self.exec_time) + \
            ", end_time: " + repr(self.end_time)


class TestJenkins(AbstractApiJenkins):
    __metaclass__ = abc.ABCMeta

    is_mocked = is_mocked

    def __init__(self, job_name_prefix):
        self.job_name_prefix = job_name_prefix
        TestJob._current_order = 1
        self.test_jobs = OrderedDict()

    @abc.abstractmethod
    def job(self, name, exec_time, max_fails, expect_invocations, expect_order, initial_buildno=None, invocation_delay=0.1, params=None,
            script=None, unknown_result=False, final_result=None, serial=False):
        pass

    @abc.abstractmethod
    def flow_job(self, name=None, params=None):
        pass

    def flow_job_name(self, name):
        # Don't create flow jobs when mocked
        name = '0flow_' + name if name else '0flow'
        return (self.job_name_prefix or '') + name

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if not exc_type:
            self.test_results()

    def test_results(self):
        print("Jenkinsflow Test Framework -- Checking results")

        max_actual_order = 0
        last_expected_order = 0
        last_end_time = 0

        for job in self.test_jobs.values():            
            if job.expect_order is not None:
                # Check job invocation order
                assert last_expected_order <= job.expect_order, "Mock job list must be sorted by expected order, error in test setup."

                assert job.actual_order >= job.expect_order, "Job: " + job.name + " was started out of order, " + \
                    "job.actual_order: " + repr(job.actual_order) + ", job.expect_order: " + repr(job.expect_order)

                if job.expect_order > last_expected_order:
                    assert job.actual_order > max_actual_order

                if job.serial:
                    assert job.invocation_time >= last_end_time, "Serial job " + job.name + " started before previous job finished"
                last_end_time = job.end_time

                last_expected_order = job.expect_order
                max_actual_order = max(job.actual_order, max_actual_order)

            if  job.expect_invocations is not None:
                # Check expected number of job invocations
                assert job.expect_invocations == job.invocation, "Job: " + job.name + " invoked " + str(job.invocation) + " times, expected " + str(job.expect_invocations) + " invocations"

            if job.unknown_result:
                # The job must still be running, but maybe it has not been started yet, so wait up to 3 seconds for it to start
                for _ in range(1, 300):
                    if job.is_running():
                        break
                    if not is_mocked:
                        time.sleep(0.01)
                        if hasattr(job, 'jenkins_resource'):
                            job.jenkins_resource.job_poll(job.name)
                        else:
                            job.poll()
                assert job.is_running(), "Job: " + job.name + " is expected to be running, but state is " + ('QUEUED' if job.is_queued() else 'IDLE')
            elif job.expect_invocations != 0:
                if job.invocation > job.max_fails:
                    expect_status = BuildResult.SUCCESS if job.final_result is None else job.final_result
                else:
                    expect_status = BuildResult.FAILURE
                build = job.get_last_build_or_none()
                assert build, "Job: " + repr(job) + " should have had build, but it has none"
                result = BuildResult[build.get_status()]
                assert result == expect_status, "Job: " + job.name + " expected result " + repr(expect_status) + " but got " + repr(result)
