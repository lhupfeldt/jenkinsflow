# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import abc
from collections import OrderedDict
import os
from os.path import join as jp

from jenkinsflow.api_base import UnknownJobException, BuildResult, Progress
from .abstract_api import AbstractApiJob, AbstractApiJenkins
from .config import test_tmp_dir


def _mkdir(path):
    try:
        os.mkdir(path)
    except OSError:
        if not os.path.exists(path):
            raise


class TestJob(AbstractApiJob, metaclass=abc.ABCMeta):
    _current_order = 1

    def __init__(self, exec_time, max_fails, expect_invocations, expect_order, initial_buildno, invocation_delay,
                 unknown_result, final_result, serial, print_env, flow_created, create_job, disappearing, non_existing, kill):
        """
        Set unknown_result to True if the result is indeterminate (timeout or invoke_unchecked)
        """
        assert exec_time > 0
        assert max_fails >= 0
        assert expect_invocations >= 0
        assert expect_order is None or expect_order >= 1
        assert initial_buildno is None or initial_buildno >= 1
        assert invocation_delay >= 0
        assert unknown_result in (False, True)
        assert serial in (False, True)
        assert flow_created in (False, True)
        assert disappearing in (False, True)
        assert non_existing in (False, True)

        self.exec_time = exec_time
        self.max_fails = max_fails
        self.expect_invocations = expect_invocations
        self.expect_order = expect_order
        self.initial_buildno = initial_buildno
        self.invocation_delay = invocation_delay
        self.unknown_result = unknown_result
        self.serial = serial
        self.print_env = print_env
        self.final_result = final_result if isinstance(final_result, (BuildResult, type(None))) else BuildResult[final_result.upper()]
        self.flow_created = flow_created
        self.create_job = create_job
        self.disappearing = disappearing
        self.non_existing = non_existing
        self.kill = kill

        self.invocation_number = 0
        self.invocation_time = self.start_time = self.end_time = 0
        self.actual_order = -1

        self.build_params = None

    @property
    def has_force_result_param(self):
        return self.max_fails > 0 or self.final_result

    def invoke(self, securitytoken, build_params, cause, description):
        self.build_params = build_params
        self.invocation_number += 1
        self.actual_order = TestJob._current_order
        TestJob._current_order += 1

    def __repr__(self):
        return ", expect_invocations: " + repr(self.expect_invocations) + \
            ", invocation_number: " + repr(self.invocation_number) + \
            ", expect_order: " + repr(self.expect_order) + \
            ", start_time: " + repr(self.start_time) + \
            ", exec_time: " + repr(self.exec_time) + \
            ", end_time: " + repr(self.end_time)


class Jobs():
    def __init__(self, api):
        self.api = api

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type:
            return None

        test_jobs = self.api.test_jobs
        for job_name, job in test_jobs.items():
            if job.flow_created:
                # Patch up another job that is supposed to be created by this job - replace job_name with job reference
                for other_job in test_jobs.values():
                    if isinstance(other_job.create_job, str):
                        other_job_name = self.api.job_name_prefix + other_job.create_job
                        if other_job_name == job_name:
                            other_job.create_job = job
                            break
                else:
                    raise Exception("Job: " + repr(job_name) + " is supposed to be created by another job, but that job was not found")

        for job_name, job in test_jobs.items():
            if job.create_job and isinstance(job.create_job, str):
                raise Exception("Job: " + repr(job_name) + " is supposed to create job: " + repr(job.create_job) + " but definition for that job was not found")


class TestJenkins(AbstractApiJenkins, metaclass=abc.ABCMeta):
    def __init__(self, job_name_prefix, **kwargs):
        super().__init__(**kwargs)
        self.job_name_prefix = job_name_prefix
        TestJob._current_order = 1
        self.test_jobs = OrderedDict()

    @abc.abstractmethod
    def job(self, name, max_fails, expect_invocations, expect_order, exec_time=None, initial_buildno=None, invocation_delay=0.1, params=None,
            script=None, unknown_result=False, final_result=None, serial=False, print_env=False, flow_created=False, create_job=None, disappearing=False,
            non_existing=False, kill=False, num_builds_to_keep=4, allow_running=False):
        """Create a job with corresponding test metadata.

        Args:
            name (str): Base name of job, the test framework will add a prefix base on test module
            exec_time (int): Number of seconds that the job will run (sleep), actual run may/will be longer
            max_fails (int): Number of times the job will fail during this flow (when using retry)
            expect_invocations (int): Number of expected invocation during this flow. Will be larger or equal to exec_time.
            ...
            flow_created (boolean): This job is expected to be non-existing at start of flow and be created during the flow
            create_job (str): Name of another job that will be created by this job, when this job is running
        """
        pass

    # Delete/Create hack sufficient to get resonable coverage on job_load test
    def delete_job(self, job_name):
        try:
            job = self.test_jobs[job_name]
            if job.non_existing:
                raise UnknownJobException(job_name)
            job.non_existing = True
        except KeyError:
            raise Exception("Test job setup error, missing test job definition:", job_name)

    def create_job(self, job_name, config_xml):
        try:
            job = self.test_jobs[job_name]
            job.non_existing = False
        except KeyError:
            raise Exception("Test job setup error, missing test job definition:", job_name)

    def job_creator(self):
        return Jobs(self)

    @abc.abstractmethod
    def flow_job(self, name=None, params=None):
        pass

    def flow_job_name(self, name):
        # Don't create flow jobs when mocked
        name = '0flow_' + name if name else '0flow'
        return (self.job_name_prefix or '') + name

    def __enter__(self):
        # pylint: disable=attribute-defined-outside-init
        self._pre_work_dir = os.getcwd()
        self._work_dir = jp(test_tmp_dir,self.job_name_prefix)
        _mkdir(self._work_dir)
        os.chdir(self._work_dir)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        os.chdir(self._pre_work_dir)
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
                assert job.expect_invocations == job.invocation_number, "Job: " + job.name + " invoked " + str(job.invocation_number) + " times, expected " + str(job.expect_invocations) + " invocations"

            if job.unknown_result:
                # The job must still be running, but maybe it has not been started yet, so wait up to 3 seconds for it to start
                max_wait_to_start = 3
                start_check_interval = 0.01
                max_wait_index = int(max_wait_to_start / start_check_interval)
                prev_progress = None
                for ii in range(1, max_wait_index):
                    # TODO: job obj should be invocation obj!
                    result, progress, last_build_number = job.job_status()
                    if progress == Progress.RUNNING:
                        break
                    if progress != prev_progress:
                        print("FW: last build status:", job.name, result, progress, last_build_number)
                        prev_progress = progress
                    self.sleep(start_check_interval)
                    if hasattr(job, 'jenkins'):
                        job.jenkins.quick_poll()
                    job.poll()

                # pylint: disable=maybe-no-member
                assert progress == Progress.RUNNING, "Job: " + job.name + " is expected to be running, but state is " + progress.name
                # Now stop the job, so that it won't be running after the testsuite is finished
                job.stop_all()
            elif job.expect_invocations != 0 and not job.kill:
                if job.invocation_number > job.max_fails:
                    expect_status = BuildResult.SUCCESS if job.final_result is None else job.final_result
                else:
                    expect_status = BuildResult.FAILURE
                # TODO job obj should be called invocation!
                # Get last obj
                try:
                    key = next(reversed(job._invocations))
                    invocation = job._invocations[key]
                except TypeError:
                    # script_api ?
                    invocation = job._invocations[-1]

                assert invocation.build_number is not None, "Job: " + repr(job) + " should have had build_number, but it has None"
                result, progress = invocation.status()
                assert result == expect_status, "Job: " + job.name + " expected result " + repr(expect_status) + " but got " + repr(result)
            elif job.kill:
                result, progress, _ = job.job_status()
                assert progress == Progress.IDLE
                # TODO
                # expect_status = BuildResult.ABORTED
                # assert result == expect_status, "Job: " + job.name + " expected result " + repr(expect_status) + " but got " + repr(result)
