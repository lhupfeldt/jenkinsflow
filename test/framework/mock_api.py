# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function
import os
from os.path import join as jp
from collections import OrderedDict

from jenkinsflow.api_base import BuildResult, Progress, UnknownJobException, ApiInvocationMixin

from .base_test_api import TestJob, TestJenkins
from jenkinsflow.test.cfg import ApiType
from .hyperspeed import HyperSpeed

here = os.path.abspath(os.path.dirname(__file__))


class MockApi(TestJenkins, HyperSpeed):
    job_xml_template = jp(here, 'job.xml.tenjin')
    api_type = ApiType.MOCK

    def __init__(self, job_name_prefix, speedup, public_uri):
        super().__init__(job_name_prefix=job_name_prefix, speedup=speedup)
        self.public_uri = public_uri
        self.username = 'dummy'
        self.password = 'dummy'

    def job(self, name, max_fails, expect_invocations, expect_order, exec_time=None, initial_buildno=None, invocation_delay=0.1, params=None,
            script=None, unknown_result=False, final_result=None, serial=False, print_env=False, flow_created=False, create_job=None,
            disappearing=False, non_existing=False, kill=False, num_builds_to_keep=4, allow_running=False, final_result_use_cli=False,
            set_build_descriptions=()):
        job_name = self.job_name_prefix + name
        assert not self.test_jobs.get(job_name)
        assert isinstance(max_fails, int)
        
        if exec_time is None:
            exec_time = 0.01

        job = MockJob(name=job_name, exec_time=exec_time, max_fails=max_fails, expect_invocations=expect_invocations, expect_order=expect_order,
                      initial_buildno=initial_buildno, invocation_delay=invocation_delay, unknown_result=unknown_result,
                      final_result=final_result, serial=serial, params=params, flow_created=flow_created, create_job=create_job,
                      disappearing=disappearing, non_existing=non_existing, kill=kill, allow_running=allow_running, api=self,
                      final_result_use_cli=final_result_use_cli, set_build_descriptions=set_build_descriptions)
        self.test_jobs[job_name] = job

    def flow_job(self, name=None, params=None):
        # Don't create flow jobs when mocked
        return self.flow_job_name(name)

    # --- Mock API ---

    def poll(self):
        pass

    def quick_poll(self):
        pass

    def queue_poll(self):
        pass

    def get_job(self, name):
        try:
            job = self.test_jobs[name]
            if job.non_existing:
                raise UnknownJobException(name)
            return job
        except KeyError:
            raise UnknownJobException(name)

    def set_build_description(self, description, replace=False, separator='\n', job_name=None, build_number=None):
        pass


class MockJob(TestJob):
    def __init__(self, name, exec_time, max_fails, expect_invocations, expect_order, initial_buildno, invocation_delay, unknown_result,
                 final_result, serial, params, flow_created, create_job, disappearing, non_existing, kill, allow_running, api, final_result_use_cli,
                 set_build_descriptions):
        super().__init__(exec_time=exec_time, max_fails=max_fails, expect_invocations=expect_invocations, expect_order=expect_order,
                                      initial_buildno=initial_buildno, invocation_delay=invocation_delay, unknown_result=unknown_result, final_result=final_result,
                                      serial=serial, print_env=False, flow_created=flow_created, create_job=create_job, disappearing=disappearing,
                                      non_existing=non_existing, kill=kill)
        self.name = name
        self.public_uri = 'http://hupfeldtit.dk/job/' + self.name
        self.build_number = None
        self.initial_build_number = initial_buildno
        self.last_build_number = initial_buildno
        self.params = params
        self._allow_running = allow_running
        self.api = api
        self.final_result_use_cli = final_result_use_cli
        self.set_build_descriptions = set_build_descriptions

        self.just_invoked = False
        self._invocation_url = 0
        self._invocations = OrderedDict()
        self.queued_why = "Why am I queued?"
        self._killed = False
        self._just_killed = False

    def job_status(self):
        latest_build_number = self._get_last_build_number_or_none()
        if self._killed:
            if not self._just_killed:
                return (BuildResult.ABORTED, Progress.IDLE, latest_build_number)
            self._just_killed = False

        if self.start_time <= self.api.time() < self.end_time:
            assert latest_build_number
            return (BuildResult.UNKNOWN, Progress.RUNNING, latest_build_number)

        if self.invocation_time <= self.api.time() < self.start_time:
            return (BuildResult.UNKNOWN, Progress.QUEUED, latest_build_number)

        # Job is finished
        if self.invocation_number <= self.max_fails:
            return (BuildResult.FAILURE, Progress.IDLE, latest_build_number)
        if self.final_result is None:
            return (BuildResult.SUCCESS, Progress.IDLE, latest_build_number)
        return (BuildResult[self.final_result.name], Progress.IDLE, latest_build_number)

    def poll(self):
        # If has been invoked and started running or already (supposed to be) finished
        if self.just_invoked and self.api.time() >= self.start_time:
            self.just_invoked = False
            self.build_number = self.last_build_number + 1 if self.last_build_number else 1
            self._invocations[self._invocation_url - 1].build_number = self.build_number

    def _get_last_build_number_or_none(self):
        self.poll()
        return self.build_number or self.last_build_number

    def _is_running(self):
        return self.start_time <= self.api.time() < self.end_time

    def invoke(self, securitytoken, build_params, cause, description):
        if not self._allow_running:
            if self._is_running():
                print("start_time:", self.start_time, "self.api.time:", self.api.time(), "end_time:", self.end_time)
                assert False

        super().invoke(securitytoken, build_params, cause, description)
        self.invocation_time = self.api.time()
        self.start_time = self.invocation_time + self.invocation_delay
        self.end_time = self.start_time + self.exec_time
        self.just_invoked = True
        self.last_build_number = self.build_number or self.last_build_number
        self.build_number = None

        inv = Invocation(self)
        inv.queued_why = "Why am I queued?"
        self._invocations[self._invocation_url] = inv
        self._invocation_url += 1
        self.poll()
        return inv

    def stop_all(self):
        for inv in self._invocations.values():
            inv.stop(False)
        if self._is_running():
            if not self._killed:
                self._just_killed = True
            self._killed = True

    def update_config(self, config_xml):
        pass

    def __repr__(self):
        return self.name + ", " + super().__repr__()


class Invocation(ApiInvocationMixin):
    def __init__(self, job):
        # _debug("queued_item_path:", queued_item_path)
        self.job = job
        self.build_number = None
        self.queued_why = None
        self._killed = False

    def status(self):
        """Result and Progress info for the invocation"""
        if self._killed:
            return (BuildResult.ABORTED, Progress.IDLE)

        if self.build_number is None:
            return (BuildResult.UNKNOWN, Progress.QUEUED)

        result, progress, _build_number = self.job.job_status()
        return result, progress

    def stop(self, dequeue):
        _, progress, _ = self.job.job_status()
        if progress == Progress.RUNNING and not dequeue:
            self._killed = True
