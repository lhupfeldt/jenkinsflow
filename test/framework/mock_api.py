# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

import os, sys, re
from os.path import join as jp
from peak.util.proxies import ObjectWrapper

here = os.path.abspath(os.path.dirname(__file__))
sys.path.extend([jp(here, '../../..'), jp(here, '../../demo')])

from jenkinsflow.jobload import update_job_from_template
from jenkinsflow.mocked import HyperSpeed

import demo_security as security

from jenkinsflow.test import cfg as test_cfg
if test_cfg.use_jenkinsapi():
    from jenkinsflow import jenkinsapi_wrapper as jenkins
else:
    from jenkinsflow import specialized_api as jenkins
from jenkinsflow.specialized_api import UnknownJobException

from jenkinsflow.unbuffered import UnBuffered
sys.stdout = UnBuffered(sys.stdout)

from .base_test_api import TestJob, TestBuild, TestJenkins
from .config import test_tmp_dir, pseudo_install_dir

_file_name_subst = re.compile(r'(_jobs|_test)?\.py')
hyperspeed = HyperSpeed()



class MockJob(TestJob):
    def __init__(self, name, exec_time, max_fails, expect_invocations, expect_order, initial_buildno=None, invocation_delay=0.01, unknown_result=False, final_result=None,
                 serial=False, params=None):
        super(MockJob, self).__init__(exec_time, max_fails, expect_invocations, expect_order, initial_buildno, invocation_delay, unknown_result, final_result, serial)
        self.name = name
        self.baseurl = 'http://hupfeldtit.dk/job/' + self.name
        self.build = Build(self, initial_buildno) if initial_buildno is not None else None
        self.params = params
        self.just_invoked = False

    @property
    def non_clickable_build_trigger_url(self):
        return self.baseurl + (' - parameters:' if self.params or self.has_force_result_param else '')

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

    def console_url(self, buildno):
        return self.baseurl + '/' + str(buildno) + '/console'

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


class WrapperJob(ObjectWrapper, TestJob):
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
        self.invocation_time = hyperspeed.time()

        if self.has_force_result_param:
            build_params = build_params or {}
            if self.invocation < self.max_fails:
                build_params['force_result'] = 'FAILURE'
            if self.invocation >= self.max_fails:
                build_params['force_result'] = 'SUCCESS' if self.final_result is None else self.final_result.name

        self.__subject__.invoke(securitytoken, build_params=build_params, cause=cause)  # pylint: disable=no-member
        TestJob.invoke(self, securitytoken, build_params, cause)



class Build(TestBuild):
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

    def console_url(self):
        return self.job.console_url(self.buildno)

    def __repr__(self):
        return self.job.name + " #" + repr(self.buildno) + " " + self.get_status()


class MockApi(TestJenkins):
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


class JenkinsTestWrapperApi(jenkins.Jenkins, TestJenkins):
    job_xml_template = jp(here, 'job.xml.tenjin')

    def __init__(self, file_name, func_name, func_num_params, job_name_prefix, reload_jobs, pre_delete_jobs, jenkinsurl, direct_url,
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
        #  Note: Use -B to avoid permission problems with .pyc files created from commandline test
        if self.func_name:
            script = "export PYTHONPATH=" + test_tmp_dir + "\n"
            script += test_cfg.skip_job_load_sh_export_str() + "\n"
            # Supply dummy args for the py.test fixtures
            dummy_args = ','.join(['0' for _ in range(self.func_num_params)])
            script += "python -Bc &quot;from jenkinsflow.test." + self.file_name.replace('.py', '') + " import *; test_" + self.func_name + "(" + dummy_args + ")&quot;"
        else:
            script = "python -B " + jp(pseudo_install_dir, 'demo', self.file_name)
        name = '0flow_' + name if name else '0flow'
        self._jenkins_job(name, exec_time=0.5, params=params, script=script)
        return (self.job_name_prefix or '') + name

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


def api(file_name, jenkinsurl=os.environ.get('JENKINS_URL') or os.environ.get('HUDSON_URL') or "http://localhost:8080", login=False):
    """Factory to create either Mock or Wrap api"""
    base_name = os.path.basename(file_name).replace('.pyc', '.py')
    job_name_prefix = _file_name_subst.sub('', base_name)
    func_name = None
    func_num_params = 0
    if '_test' in file_name:
        func_name = sys._getframe().f_back.f_code.co_name  # pylint: disable=protected-access
        func_num_params = sys._getframe().f_back.f_code.co_argcount  # pylint: disable=protected-access
        file_name = base_name
        func_name = func_name.replace('test_', '')
        assert func_name[0:len(job_name_prefix)] == job_name_prefix, \
            "Naming standard not followed: " + repr('test_' + func_name) + " defined in file: " + repr(base_name) + " should be 'test_" + job_name_prefix + "_<sub test>'"
        job_name_prefix = 'jenkinsflow_test__' + func_name + '__'
    else:
        job_name_prefix = 'jenkinsflow_demo__' + job_name_prefix + '__'
        file_name = base_name.replace('_jobs', '')

    print()
    print("--- Preparing api for ", repr(job_name_prefix), "---")
    global hyperspeed
    hyperspeed = HyperSpeed()
    if hyperspeed.is_mocked:
        print('Using Mocked API')
        return MockApi(job_name_prefix, jenkinsurl)
    else:
        print('Using Real Jenkins API with wrapper')
        reload_jobs = not test_cfg.skip_job_load()
        pre_delete_jobs = not test_cfg.skip_job_delete()
        direct_url = test_cfg.direct_url()
        return JenkinsTestWrapperApi(file_name, func_name, func_num_params, job_name_prefix, reload_jobs, pre_delete_jobs,
                                     jenkinsurl, direct_url, security.username, security.password, security.securitytoken, login=login)
