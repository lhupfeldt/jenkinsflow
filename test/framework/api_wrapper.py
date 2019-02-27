# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import sys, time, os
from os.path import join as jp

from objproxies import ObjectWrapper

from jenkinsflow.api_base import UnknownJobException
from jenkinsflow import script_api
from jenkinsflow import jenkins_api
from jenkinsflow.jobload import update_job_from_template
from jenkinsflow.test import cfg as test_cfg
from jenkinsflow.test.cfg import ApiType

import demo_security as security  # pylint: disable=import-error

from .base_test_api import TestJob, TestJenkins, Jobs as TestJobs
from .config import test_tmp_dir, pseudo_install_dir
from .mock_api import MockJob


here = os.path.abspath(os.path.dirname(__file__))


class WrapperJob(TestJob, ObjectWrapper):
    # NOTE: ObjectWrapper class requires all attributes which are NOT proxied to be declared statically and overridden at instance level
    exec_time = None
    max_fails = None
    expect_invocations = None
    expect_order = None
    unknown_result = None
    final_result = None
    final_result_use_cli = None
    serial = None
    disappearing = None
    non_existing = None
    kill = None

    mock_job = None

    invocation_number = None
    invocation_time = None
    invocation_delay = None
    end_time = None
    actual_order = None

    def __init__(self, jenkins_job, mock_job):
        ObjectWrapper.__init__(self, jenkins_job)
        TestJob.__init__(self, exec_time=mock_job.exec_time, max_fails=mock_job.max_fails,
                         expect_invocations=mock_job.expect_invocations, expect_order=mock_job.expect_order,
                         initial_buildno=mock_job.initial_buildno, invocation_delay=mock_job.invocation_delay,
                         unknown_result=mock_job.unknown_result, final_result=mock_job.final_result, serial=mock_job.serial,
                         print_env=False, flow_created=mock_job.flow_created, create_job=mock_job.create_job, disappearing=mock_job.disappearing,
                         non_existing=mock_job.non_existing, kill=mock_job.kill)

    def invoke(self, securitytoken, build_params, cause, description):
        self.invocation_time = time.time()
        if self.disappearing:
            # Delete the job to fake a job that disappears while a flow is running
            print("Deleting disappearing job:", self.name)
            self.jenkins.delete_job(self.name)
            self.jenkins.poll()

        if self.has_force_result_param:
            build_params = build_params or {}
            if self.invocation_number < self.max_fails:
                build_params['force_result'] = 'FAILURE'
            if self.invocation_number >= self.max_fails:
                build_params['force_result'] = 'SUCCESS' if self.final_result is None else self.final_result.name

        invocation = self.__subject__.invoke(securitytoken, build_params=build_params, cause=cause, description=description)  # pylint: disable=no-member
        TestJob.invoke(self, securitytoken, build_params, cause, description)
        return invocation


class Jobs(TestJobs):
    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type:
            return None
        super().__exit__(exc_type, exc_value, traceback)
        test_jobs = self.api.test_jobs
        for job_name, job in test_jobs.items():
            if not (job.flow_created or job.non_existing):
                self.api._jenkins_job(job_name, job.exec_time, job.params, None, job.print_env, job.create_job,
                                      always_load=job.disappearing, num_builds_to_keep=4, final_result_use_cli=False,
                                      set_build_descriptions=job.set_build_descriptions)


class _TestWrapperApi():
    def __init__(self, file_name, func_name, func_num_params, reload_jobs, pre_delete_jobs, securitytoken, direct_url, fake_public_uri):
        self.file_name = file_name
        self.func_name = func_name
        self.func_num_params = func_num_params
        self.reload_jobs = reload_jobs
        self.pre_delete_jobs = pre_delete_jobs
        self.securitytoken = securitytoken
        self.direct_url = direct_url
        self.fake_public_uri = fake_public_uri
        self.using_job_creator = False

    def _jenkins_job(self, name, exec_time, params, script, print_env, create_job, always_load, num_builds_to_keep,
                     final_result_use_cli, set_build_descriptions):
        # Create job in Jenkins
        if self.reload_jobs or always_load:
            context = dict(
                exec_time=exec_time,
                params=params or (),
                script=script,
                pseudo_install_dir=pseudo_install_dir,
                securitytoken=self.securitytoken,
                username=security.username,
                password=security.password,
                direct_url=self.direct_url,
                print_env=print_env,
                create_job=create_job,
                test_file_name=self.file_name,
                test_tmp_dir=test_tmp_dir, api_type=self.api_type,
                num_builds_to_keep=num_builds_to_keep,
                final_result_use_cli=final_result_use_cli,
                set_build_descriptions=set_build_descriptions,
            )
            update_job_from_template(self.job_loader_jenkins, name, self.job_xml_template, pre_delete=self.pre_delete_jobs, context=context)

    def job(self, name, max_fails, expect_invocations, expect_order, exec_time=None, initial_buildno=None, invocation_delay=0.1, params=None,
            script=None, unknown_result=False, final_result=None, serial=False, print_env=False, flow_created=False, create_job=None, disappearing=False,
            non_existing=False, kill=False, num_builds_to_keep=4, allow_running=False, final_result_use_cli=False,
            set_build_descriptions=()):
        job_name = self.job_name_prefix + name
        assert not self.test_jobs.get(job_name)
        assert isinstance(max_fails, int)

        if create_job or flow_created:
            assert self.using_job_creator

        if exec_time is None:
            exec_time = 0.01

        if max_fails > 0 or final_result:
            params = list(params) if params else []
            force_result_desc = 'Caller can force job to success, fail or unstable.\n' \
                                'If "ABORTED" is specified the job should never run to the end, but be aborted before that.\n' \
                                'If this does not happen, the job will fail.'
            params.append(('force_result', ('SUCCESS', 'FAILURE', 'UNSTABLE', 'ABORTED'), force_result_desc))

        if flow_created or non_existing:
            try:
                print("Deleting job:", job_name)
                self.job_loader_jenkins.delete_job(job_name)
            except UnknownJobException:
                pass
        elif not self.using_job_creator and not non_existing:
            # TODO: Remove and convert all to use job_creator?
            self._jenkins_job(job_name, exec_time, params, script, print_env, create_job=create_job, always_load=disappearing,
                              num_builds_to_keep=num_builds_to_keep, final_result_use_cli=final_result_use_cli,
                              set_build_descriptions=set_build_descriptions)

        job = MockJob(name=job_name, exec_time=exec_time, max_fails=max_fails, expect_invocations=expect_invocations, expect_order=expect_order,
                      initial_buildno=initial_buildno, invocation_delay=invocation_delay, unknown_result=unknown_result, final_result=final_result,
                      serial=serial, params=params, flow_created=flow_created, create_job=create_job, disappearing=disappearing,
                      non_existing=non_existing, kill=kill, allow_running=allow_running, api=self, final_result_use_cli=final_result_use_cli,
                      set_build_descriptions=set_build_descriptions)
        self.test_jobs[job_name] = job

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
        if self.api_type == ApiType.SCRIPT:
            return job_name

        #  Note: Use -B to avoid permission problems with .pyc files created from commandline test
        if self.func_name:
            script = "export PYTHONPATH=" + test_tmp_dir + "\n"
            script += test_cfg.skip_job_load_sh_export_str() + "\n"
            # script += "export " + ApiType.JENKINS.env_name() + "=true\n"  # pylint: disable=no-member
            # Supply dummy args for the py.test fixtures
            dummy_args = ','.join(['0' for _ in range(self.func_num_params)])
            script += sys.executable + " -Bc &quot;import sys; from jenkinsflow.test." + self.file_name.replace('.py', '') + " import *; sys.exit(test_" + self.func_name + "(" + dummy_args + "))&quot;"
        else:
            script = sys.executable + " -B " + jp(pseudo_install_dir, 'demo', self.file_name)
        self._jenkins_job(job_name, exec_time=0.5, params=params, script=script, print_env=False, create_job=None, always_load=False,
                          num_builds_to_keep=4, final_result_use_cli=False, set_build_descriptions=())
        return job_name

    def job_creator(self):
        self.using_job_creator = True
        return Jobs(self)

    # --- Wrapped API ---

    def delete_job(self, job_name):
        TestJenkins.delete_job(self, job_name)
        self.job_loader_jenkins.delete_job(job_name)

    def create_job(self, job_name, config_xml):
        TestJenkins.create_job(self, job_name, config_xml)
        self.job_loader_jenkins.create_job(job_name, config_xml)

    def get_job(self, name):
        job = None
        try:
            job = self.test_jobs.get(name)
            jenkins_job = super().get_job(name)
            if job is None or job.non_existing:
                msg = "InternalError in api_wrapper get_job. Job exists in Jenkins"
                if job is None:
                    msg += ", but not in test_jobs: " + repr(name)
                else:
                    msg += ", but test job has property non_existing: " + repr(name) + ", test job:" + repr(job)
                print(msg, file=sys.stderr)
                raise Exception(msg)

            if isinstance(job, MockJob):
                self.test_jobs[name] = job = WrapperJob(jenkins_job, job)
            assert isinstance(job, WrapperJob)
            job.__subject__ = jenkins_job
            return job
        except UnknownJobException as ex:
            if job and not (job.flow_created or job.non_existing):
                print(ex, file=sys.stderr)
                msg = "In api_wrapper get_job. Job exists in test_jobs, but not in in Jenkins: " + repr(name)
                print(msg, file=sys.stderr)
                raise Exception(msg)
            raise

    def poll(self):
        super().poll()
        if self.fake_public_uri:
            self._public_uri = self.fake_public_uri


class JenkinsTestWrapperApi(_TestWrapperApi, jenkins_api.Jenkins, TestJenkins):
    api_type = ApiType.JENKINS
    job_xml_template = jp(here, 'job.xml.tenjin')

    def __init__(self, file_name, func_name, func_num_params, job_name_prefix, reload_jobs, pre_delete_jobs, direct_url, fake_public_uri,
                 username, password, securitytoken, login, invocation_class):
        TestJenkins.__init__(self, job_name_prefix=job_name_prefix)
        if login:
            jenkins_api.Jenkins.__init__(self, direct_uri=direct_url, job_prefix_filter=job_name_prefix, username=username, password=password,
                                         invocation_class=invocation_class)
        else:
            jenkins_api.Jenkins.__init__(self, direct_uri=direct_url, job_prefix_filter=job_name_prefix, invocation_class=invocation_class)
        self.job_loader_jenkins = jenkins_api.Jenkins(direct_uri=direct_url, job_prefix_filter=job_name_prefix, username=username, password=password)
        _TestWrapperApi.__init__(self, file_name, func_name, func_num_params, reload_jobs, pre_delete_jobs, securitytoken, direct_url, fake_public_uri)


class ScriptTestWrapperApi(_TestWrapperApi, script_api.Jenkins, TestJenkins):
    api_type = ApiType.SCRIPT
    job_xml_template = jp(here, 'job_script.py.tenjin')

    def __init__(self, file_name, func_name, func_num_params, job_name_prefix, reload_jobs, pre_delete_jobs, direct_url, fake_public_uri,
                 username, password, securitytoken, login, invocation_class):
        TestJenkins.__init__(self, job_name_prefix=job_name_prefix)
        if login:
            script_api.Jenkins.__init__(self, direct_uri=direct_url, job_prefix_filter=job_name_prefix, username=username, password=password,
                                        invocation_class=invocation_class)
        else:
            script_api.Jenkins.__init__(self, direct_uri=direct_url, job_prefix_filter=job_name_prefix, invocation_class=invocation_class)
        self.job_loader_jenkins = script_api.Jenkins(direct_uri=direct_url, job_prefix_filter=job_name_prefix, username=username, password=password)
        _TestWrapperApi.__init__(self, file_name, func_name, func_num_params, reload_jobs, pre_delete_jobs, securitytoken, direct_url, fake_public_uri)
