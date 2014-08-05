# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

import os, sys, time
from os.path import join as jp

from peak.util.proxies import ObjectWrapper  # pylint: disable=import-error

from jenkinsflow.jobload import update_job_from_template
import demo_security as security  # pylint: disable=import-error
from jenkinsflow.test import cfg as test_cfg
from jenkinsflow.test.cfg import ApiType


api_type = test_cfg.selected_api()
here = os.path.abspath(os.path.dirname(__file__))

if api_type == ApiType.SPECIALIZED:
    from jenkinsflow import specialized_api as jenkins
    _job_xml_template = jp(here, 'job.xml.tenjin')
elif api_type == ApiType.JENKINSAPI:
    from jenkinsflow import jenkinsapi_wrapper as jenkins
    _job_xml_template = jp(here, 'job.xml.tenjin')
elif api_type == ApiType.SCRIPT:
    from jenkinsflow import script_api as jenkins
    _job_xml_template = jp(here, 'job_script.py.tenjin')
else:
    raise Exception("Don't know which API to use!")

from jenkinsflow.api_base import UnknownJobException

from .base_test_api import TestJob, TestJenkins, Jobs as TestJobs
from .config import test_tmp_dir, pseudo_install_dir
from .mock_api import MockJob


class WrapperJob(ObjectWrapper, TestJob, jenkins.ApiJob):
    # NOTE: ObjectWrapper class requires all attributes which are NOT proxied to be declared statically and overridden at instance level
    exec_time = None
    max_fails = None
    expect_invocations = None
    expect_order = None
    unknown_result = None
    final_result = None
    serial = None

    mock_job = None

    invocation = None
    invocation_time = None
    invocation_delay = None
    end_time = None
    actual_order = None

    def __init__(self, jenkins_job, mock_job):
        ObjectWrapper.__init__(self, jenkins_job)
        TestJob.__init__(self, exec_time=mock_job.exec_time, max_fails=mock_job.max_fails,
                         expect_invocations=mock_job.expect_invocations, expect_order=mock_job.expect_order,
                         initial_buildno=mock_job.initial_buildno, invocation_delay=mock_job.invocation_delay,
                         unknown_result=mock_job.unknown_result, final_result=mock_job.final_result, serial=mock_job.serial)

    def invoke(self, securitytoken=None, build_params=None, cause=None):
        self.invocation_time = time.time()

        if self.has_force_result_param:
            build_params = build_params or {}
            if self.invocation < self.max_fails:
                build_params['force_result'] = 'FAILURE'
            if self.invocation >= self.max_fails:
                build_params['force_result'] = 'SUCCESS' if self.final_result is None else self.final_result.name

        self.__subject__.invoke(securitytoken, build_params=build_params, cause=cause)  # pylint: disable=no-member
        TestJob.invoke(self, securitytoken, build_params, cause)


class Jobs(TestJobs):
    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type:
            return None
        super(Jobs, self).__exit__(exc_type, exc_value, traceback)
        test_jobs = self.api.test_jobs
        for job_name, job in test_jobs.iteritems():
            if not job.flow_created:
                self.api._jenkins_job(job_name, job.exec_time, job.params, None, job.print_env, job.create_job)


class JenkinsTestWrapperApi(jenkins.Jenkins, TestJenkins):
    job_xml_template = _job_xml_template
    api_type = api_type

    def __init__(self, file_name, func_name, func_num_params, job_name_prefix, reload_jobs, pre_delete_jobs, direct_url,
                 username, password, securitytoken, login):
        TestJenkins.__init__(self, job_name_prefix=job_name_prefix)
        if login:
            jenkins.Jenkins.__init__(self, direct_uri=direct_url, job_prefix_filter=job_name_prefix, username=username, password=password)
        else:
            jenkins.Jenkins.__init__(self, direct_uri=direct_url, job_prefix_filter=job_name_prefix)
        self.job_loader_jenkins = jenkins.Jenkins(direct_uri=direct_url, job_prefix_filter=job_name_prefix, username=username, password=password)

        self.file_name = file_name
        self.func_name = func_name
        self.func_num_params = func_num_params
        self.reload_jobs = reload_jobs
        self.pre_delete_jobs = pre_delete_jobs
        self.securitytoken = securitytoken
        self.direct_url = direct_url
        self.using_job_creator = False

    def _jenkins_job(self, name, exec_time, params, script, print_env, create_job):
        # Create job in Jenkins
        if self.reload_jobs:
            context = dict(exec_time=exec_time, params=params or (), script=script, pseudo_install_dir=pseudo_install_dir,
                           securitytoken=self.securitytoken, username=security.username, password=security.password, direct_url=self.direct_url,
                           print_env=print_env,
                           create_job=create_job,
                           test_file_name=self.file_name,
                           test_tmp_dir=test_tmp_dir, api_type=self.api_type)
            update_job_from_template(self.job_loader_jenkins, name, self.job_xml_template, pre_delete=self.pre_delete_jobs, context=context)

    def job(self, name, exec_time, max_fails, expect_invocations, expect_order, initial_buildno=None, invocation_delay=0.1, params=None,
            script=None, unknown_result=False, final_result=None, serial=False, print_env=False, flow_created=False, create_job=None):
        job_name = self.job_name_prefix + name
        assert not self.test_jobs.get(job_name)

        if create_job or flow_created:
            assert self.using_job_creator

        if max_fails > 0 or final_result:
            params = list(params) if params else []
            params.append(('force_result', ('SUCCESS', 'FAILURE', 'UNSTABLE', 'ABORTED'), 'Caller can force job to success, fail, unstable or aborted'))

        if flow_created:
            try:
                print("Deleting job:", job_name)
                self.job_loader_jenkins.delete_job(job_name)
            except UnknownJobException:
                pass
        elif not self.using_job_creator:
            # TODO: Remove and convert all to use job_creator?
            self._jenkins_job(job_name, exec_time, params, script, print_env, create_job=create_job)

        self.test_jobs[job_name] = MockJob(name=job_name, exec_time=exec_time, max_fails=max_fails, expect_invocations=expect_invocations, expect_order=expect_order,
                                           initial_buildno=initial_buildno, invocation_delay=invocation_delay,
                                           unknown_result=unknown_result, final_result=final_result, serial=serial, params=params,
                                           flow_created=flow_created, create_job=create_job)

    def flow_job(self, name=None, params=None):
        """
        Creates a flow job
        For running demo/test flow script as jenkins job
        Requires jenkinsflow to be copied to 'pseudo_install_dir' and all jobs to be loaded beforehand (e.g. test.py has been run)
        Returns job name
        """
        name = '0flow_' + name if name else '0flow'
        job_name = (self.job_name_prefix or '') + name
        # TODO Handle script api
        if api_type == ApiType.SCRIPT:
            return job_name

        #  Note: Use -B to avoid permission problems with .pyc files created from commandline test
        if self.func_name:
            script = "export PYTHONPATH=" + test_tmp_dir + "\n"
            script += test_cfg.skip_job_load_sh_export_str() + "\n"
            # Supply dummy args for the py.test fixtures
            dummy_args = ','.join(['0' for _ in range(self.func_num_params)])
            script += sys.executable + " -Bc &quot;from jenkinsflow.test." + self.file_name.replace('.py', '') + " import *; test_" + self.func_name + "(" + dummy_args + ")&quot;"
        else:
            script = sys.executable + " -B " + jp(pseudo_install_dir, 'demo', self.file_name)
        self._jenkins_job(job_name, exec_time=0.5, params=params, script=script, print_env=False, create_job=None)
        return job_name

    def job_creator(self):
        self.using_job_creator = True
        return Jobs(self)

    # --- Wrapped API ---

    def delete_job(self, job_name):
        self.job_loader_jenkins.delete_job(job_name)

    def create_job(self, job_name, config_xml):
        self.job_loader_jenkins.create_job(job_name, config_xml)

    def get_job(self, name):
        job = None
        try:
            job = self.test_jobs.get(name)
            jenkins_job = super(JenkinsTestWrapperApi, self).get_job(name)
            if not job:
                raise Exception("InternalError in api_wrapper get_job. Job exists in Jenkins, but not in test_jobs: " + repr(name))
                
            if isinstance(job, MockJob):
                self.test_jobs[name] = job = WrapperJob(jenkins_job, job)
            assert isinstance(job, WrapperJob)
            job.__subject__ = jenkins_job
            return job
        except UnknownJobException as ex:
            if job:
                print(ex, file=sys.stderr)
                print("In api_wrapper get_job. Job exists in test_jobs, but not in in Jenkins: " + repr(name))
            raise
