# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import os, sys, time
from os.path import join as jp

from peak.util.proxies import ObjectWrapper

from jenkinsflow.jobload import update_job_from_template
import demo_security as security
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

from jenkinsflow.api_base import UnknownJobException, ApiJobMixin

from .base_test_api import TestJob, TestJenkins
from .config import test_tmp_dir, pseudo_install_dir
from .mock_api import MockJob


class WrapperJob(ObjectWrapper, TestJob, ApiJobMixin):
    # NOTE: ObjectWrapper class requires all attributes which are NOT proxied to be declared statically and overridden at instance level
    exec_time = None
    max_fails = None
    expect_invocations = None
    expect_order = None
    unknown_result = None
    final_result = None
    serial = None

    invocation = None
    invocation_time = None
    invocation_delay = None
    end_time = None
    actual_order = None

    def __init__(self, jenkins_job, exec_time, max_fails, expect_invocations, expect_order, unknown_result, final_result, serial):
        ObjectWrapper.__init__(self, jenkins_job)
        TestJob.__init__(self, exec_time=exec_time, max_fails=max_fails, expect_invocations=expect_invocations, expect_order=expect_order,
                         initial_buildno=None, invocation_delay=0.01, unknown_result=unknown_result, final_result=final_result, serial=serial)

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

    def _jenkins_job(self, name, exec_time, params, script):
        name = self.job_name_prefix + name
        assert not self.test_jobs.get(name)
        # Create job in Jenkins
        if self.reload_jobs:
            context = dict(exec_time=exec_time, params=params or (), script=script, pseudo_install_dir=pseudo_install_dir,
                           securitytoken=self.securitytoken, username=security.username, password=security.password, direct_url=self.direct_url)
            update_job_from_template(self.job_loader_jenkins, name, self.job_xml_template, pre_delete=self.pre_delete_jobs, context=context)
        return name

    def job(self, name, exec_time, max_fails, expect_invocations, expect_order, initial_buildno=None, invocation_delay=0.1, params=None,
            script=None, unknown_result=False, final_result=None, serial=False):
        if max_fails > 0 or final_result:
            params = list(params) if params else []
            params.append(('force_result', ('SUCCESS', 'FAILURE', 'UNSTABLE'), 'Caller can force job to success, fail or unstable'))
        name = self._jenkins_job(name, exec_time, params, script)
        self.test_jobs[name] = MockJob(name, exec_time, max_fails, expect_invocations, expect_order, initial_buildno, invocation_delay, unknown_result, final_result, serial, params)

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
            script += "python -Bc &quot;from jenkinsflow.test." + self.file_name.replace('.py', '') + " import *; test_" + self.func_name + "(" + dummy_args + ")&quot;"
        else:
            script = "python -B " + jp(pseudo_install_dir, 'demo', self.file_name)
        self._jenkins_job(name, exec_time=0.5, params=params, script=script)
        return job_name

    # --- Wrapped API ---

    def delete_job(self, job_name):
        self.job_loader_jenkins.delete_job(job_name)

    def create_job(self, job_name, config_xml):
        self.job_loader_jenkins.create_job(job_name, config_xml)

    def get_job(self, name):
        try:
            job = self.test_jobs[name]
            jenkins_job = super(JenkinsTestWrapperApi, self).get_job(name)
            if isinstance(job, MockJob):
                self.test_jobs[name] = job = WrapperJob(jenkins_job, job.exec_time, job.max_fails, job.expect_invocations, job.expect_order, job.unknown_result, job.final_result, job.serial)
            assert isinstance(job, WrapperJob)
            job.__subject__ = jenkins_job
            return job
        except KeyError:
            raise UnknownJobException(name)
