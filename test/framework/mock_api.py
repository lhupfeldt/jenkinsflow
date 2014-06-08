# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function
import os
from os.path import join as jp

from jenkinsflow.api_base import UnknownJobException, ApiJobMixin, ApiBuildMixin
from jenkinsflow.mocked import hyperspeed

from .base_test_api import TestJob, TestBuild, TestJenkins

here = os.path.abspath(os.path.dirname(__file__))


class MockJob(TestJob, ApiJobMixin):
    def __init__(self, name, exec_time, max_fails, expect_invocations, expect_order, initial_buildno=None, invocation_delay=0.01, unknown_result=False, final_result=None,
                 serial=False, params=None):
        super(MockJob, self).__init__(exec_time, max_fails, expect_invocations, expect_order, initial_buildno, invocation_delay, unknown_result, final_result, serial)
        self.name = name
        self.public_uri = self.baseurl = 'http://hupfeldtit.dk/job/' + self.name
        self.build = Build(self, initial_buildno) if initial_buildno is not None else None
        self.params = params
        self.just_invoked = False

    @property
    def non_clickable_build_trigger_url(self):
        return self.baseurl

    def is_running(self):
        return self.start_time <= hyperspeed.time() < self.end_time

    def is_queued(self):
        return self.invocation_time <= hyperspeed.time() < self.start_time

    def poll(self):
        # If has been invoked and started running or already (supposed to be) finished
        if self.just_invoked and self.end_time and hyperspeed.time() >= self.start_time:
            self.just_invoked = False

            if self.build is None:
                self.build = Build(self, 1)
                return

            self.build = Build(self, self.build.buildno + 1)

    def get_last_build_or_none(self):
        self.poll()
        return self.build

    def invoke(self, securitytoken=None, build_params=None, cause=None):
        super(MockJob, self).invoke(securitytoken, build_params, cause)
        assert not self.is_running()
        self.invocation_time = hyperspeed.time()
        self.start_time = self.invocation_time + self.invocation_delay
        self.end_time = self.start_time + self.exec_time
        self.just_invoked = True

    def update_config(self, config_xml):
        pass

    def __repr__(self):
        return self.name + ", " + super(MockJob, self).__repr__()


class Build(ApiBuildMixin, TestBuild):
    def __init__(self, job, initial_buildno):
        self.job = job
        self.buildno = initial_buildno

    def is_running(self):
        return self.job.is_running()

    def get_status(self):
        if self.job.invocation <= self.job.max_fails:
            return 'FAILURE'
        if self.job.final_result is None:
            return 'SUCCESS'
        return self.job.final_result.name

    def __repr__(self):
        return self.job.name + " #" + repr(self.buildno) + " " + self.get_status()


class MockApi(TestJenkins):
    job_xml_template = jp(here, 'job.xml.tenjin')

    def __init__(self, job_name_prefix, baseurl):
        super(MockApi, self).__init__(job_name_prefix)
        self.baseurl = baseurl
        self._deleted_jobs = {}

    def job(self, name, exec_time, max_fails, expect_invocations, expect_order, initial_buildno=None, invocation_delay=0.1, params=None,
            script=None, unknown_result=False, final_result=None, serial=False):
        name = self.job_name_prefix + name
        assert not self.test_jobs.get(name)
        self.test_jobs[name] = MockJob(name, exec_time, max_fails, expect_invocations, expect_order, initial_buildno, invocation_delay, unknown_result, final_result, serial, params)

    def flow_job(self, name=None, params=None):
        # Don't create flow jobs when mocked
        return self.flow_job_name(name)

    # --- Mock API ---

    def poll(self):
        pass

    def quick_poll(self):
        pass

    # Delete/Create hack sufficient to get resonable coverage on job_load test
    def delete_job(self, job_name):
        try:
            self._deleted_jobs[job_name] = self.test_jobs[job_name]
        except KeyError:
            raise UnknownJobException(job_name)
        del self.test_jobs[job_name]

    def create_job(self, job_name, config_xml):
        if not job_name in self.test_jobs:
            self.test_jobs[job_name] = self._deleted_jobs[job_name]

    def get_job(self, name):
        try:
            return self.test_jobs[name]
        except KeyError:
            raise UnknownJobException(name)
