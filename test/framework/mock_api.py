from __future__ import print_function

import os, sys, abc, re
from collections import OrderedDict
import time
from os.path import join as jp
from peak.util.proxies import ObjectWrapper

here = os.path.abspath(os.path.dirname(__file__))
sys.path.extend([jp(here, '../../..'), jp(here, '../../demo')])
import demo_security as security

import jenkinsapi
from jenkinsapi import jenkins

from clean_jobs_state import clean_jobs_state
from jenkinsflow.unbuffered import UnBuffered
sys.stdout = UnBuffered(sys.stdout)

from jenkinsflow.jobload import update_job_from_template

_file_name_subst = re.compile(r'(_jobs|_test)?\.py')


class MockJob(object):
    _current_order = 1

    def __init__(self, name, exec_time, max_fails, expect_invocations, expect_order, initial_buildno=0, invocation_delay=0.01):
        """Set max_fails to -1 for an unchecked invocation"""
        assert exec_time > 0
        assert invocation_delay > 0
        self.name = name
        self.exec_time = exec_time
        self.max_fails = max_fails
        self.expect_invocations = expect_invocations
        self.expect_order = expect_order
        self.invocation = 0
        self.invocation_time = self.start_time = self.end_time = 0
        self.invocation_delay = invocation_delay
        self.base_url = 'http://hupfeldtit.dk/jobs/' + self.name
        self.just_invoked = False
        self.actual_order = -1
        self.debug('__init__')
        self.build = Build(self, initial_buildno)

    def debug(self, what):
        # print("Mock job: ", what, self, "time:", time.time())
        pass

    def get_build_triggerurl(self):
        return self.base_url + '/hello/build'

    def is_running(self):
        running = self.start_time < time.time() < self.end_time
        self.debug('is_running: ' + repr(running))
        return running

    def is_queued(self):
        queued = self.invocation_time < time.time() < self.start_time
        self.debug('is_queued: ' + repr(queued))
        return queued

    def poll(self):
        # self.debug('poll')
        if self.is_running():
            # self.debug('poll: job is running')
            if self.just_invoked:
                self.build.buildno = self.build.buildno + self.invocation
                self.debug('poll: new buildno ' + repr(self.build.buildno))
                self.just_invoked = False

    def get_last_build_or_none(self):
        self.debug('get_last_build_or_none')
        return self.build if self.build.buildno else None

    def invoke(self, securitytoken=None, block=False, skip_if_running=False, invoke_pre_check_delay=3,  # pylint: disable=unused-argument
               invoke_block_delay=15, build_params=None, cause=None, files=None):
        self.just_invoked = True
        self.actual_order = MockJob._current_order
        MockJob._current_order += 1
        self.invocation += 1
        self.invocation_time = time.time()
        self.start_time = self.invocation_time + self.invocation_delay
        self.end_time = self.start_time + self.exec_time
        self.debug('invoke')

    def update_config(self, config_xml):
        pass

    def __repr__(self):
        return self.name + \
            ", expect_invocations: " + repr(self.expect_invocations) + \
            ", invocation: " + repr(self.invocation) + \
            ", expect_order: " + repr(self.expect_order) + \
            ", start_time: " + repr(self.start_time) + \
            ", exec_time: " + repr(self.exec_time) + \
            ", end_time: " + repr(self.end_time)


class WrapperJob(ObjectWrapper):
    _current_order = 1

    name = None
    exec_time = None
    max_fails = None
    expect_invocations = None
    expect_order = None
    invocation = None
    invocation_time = None
    invocation_delay = None
    actual_order = None

    def __init__(self, jenkins_job, name, exec_time, max_fails, expect_invocations, expect_order):
        """Set max_fails to -1 for an unchecked invocation"""
        assert exec_time > 0
        self.name = name
        self.exec_time = exec_time
        self.max_fails = max_fails
        self.expect_invocations = expect_invocations
        self.expect_order = expect_order
        self.invocation = 0
        self.invocation_time = 0
        self.actual_order = -1
        ObjectWrapper.__init__(self, jenkins_job)

    def invoke(self, securitytoken=None, block=False, skip_if_running=False, invoke_pre_check_delay=3,  # pylint: disable=unused-argument
               invoke_block_delay=15, build_params=None, cause=None, files=None):
        self.actual_order = WrapperJob._current_order
        WrapperJob._current_order += 1
        self.invocation += 1
        self.invocation_time = time.time()
        self.__subject__.invoke(securitytoken, block, skip_if_running, invoke_pre_check_delay,  # pylint: disable=no-member
                                invoke_block_delay, build_params, cause, files)


class Build(object):
    def __init__(self, job, initial_buildno):
        self.job = job
        self.buildno = initial_buildno
        self.debug('__init__')

    def debug(self, what):
        print("Mock build: ", what, self, "time:", time.time())

    def is_running(self):
        return self.job.is_running()

    def get_status(self):
        return 'PASSED' if self.is_good() else 'FAILED'

    def get_result_url(self):
        return self.job.base_url + '/mock/build/status'

    def is_good(self):
        return self.job.invocation > self.job.max_fails

    def __repr__(self):
        return self.job.name + " #" + repr(self.buildno) + " " + self.get_status()


class _JobsMixin(object):
    __metaclass__ = abc.ABCMeta
    job_xml_template = jp(here, 'job.xml.tenjin')

    @abc.abstractmethod
    def job(self, name, exec_time, max_fails, expect_invocations, expect_order, initial_buildno=0, invocation_delay=0.1, params=None, script=None):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if not exc_type:
            self.test_results()

    @property
    def is_mocked(self):
        return is_mocked()

    def test_results(self):
        print("Jenkinsflow Test Framework -- Checking results")

        max_actual_order = 0
        last_expected_order = 0

        for job in self._jf_jobs.values():
            if job.expect_order is not None:
                # Check job invocation order
                assert last_expected_order <= job.expect_order, "Mock job list must be sorted by expected order, error in test setup."

                assert job.actual_order >= job.expect_order, "Job: " + job.name + " was started out of order, " + \
                    "job.actual_order: " + repr(job.actual_order) + ", job.expect_order: " + repr(job.expect_order)

                if job.expect_order > last_expected_order:
                    assert job.actual_order > max_actual_order

                last_expected_order = job.expect_order
                max_actual_order = max(job.actual_order, max_actual_order)

            if job.max_fails == -1:
                # Unchecked job
                continue

            # Check expected number of job invocations
            assert job.expect_invocations == job.invocation, "Job: " + job.name + " invoked " + str(job.invocation) + " times, expected " + str(job.expect_invocations) + " invocations"
            if job.invocation > job.max_fails:
                assert job.get_last_build_or_none().is_good(), "Job: " + job.name + " should have been in state good, but it is not"
            elif job.expect_invocations != 0:
                assert not job.get_last_build_or_none().is_good(), "Job: " + job.name + " should have been in failed state, but it is not"


class MockApi(_JobsMixin):
    def __init__(self, job_name_prefix):
        self.job_name_prefix = job_name_prefix
        MockJob._current_order = 1
        self._jf_jobs = OrderedDict()

    def job(self, name, exec_time, max_fails, expect_invocations, expect_order, initial_buildno=0, invocation_delay=0.1, params=None, script=None):
        name = self.job_name_prefix + name
        assert not self._jf_jobs.get(name)
        self._jf_jobs[name] = MockJob(name, exec_time, max_fails, expect_invocations, expect_order, initial_buildno, invocation_delay)

    def flow_job(self, name=None, params=None):
        # Don't create flow jobs when mocked
        pass

    # --- Mock API ---

    def poll(self):
        pass

    def delete_job(self, job_name):
        del self._jf_jobs[job_name]

    def create_job(self, job_name, config_xml):
        pass

    def get_job(self, name):
        try:
            return self._jf_jobs[name]
        except KeyError:
            raise jenkinsapi.custom_exceptions.UnknownJob(name)


class JenkinsWrapperApi(jenkins.Jenkins, _JobsMixin):
    def __init__(self, file_name, func_name, job_name_prefix, reload_jobs, jenkinsurl, username, password, securitytoken):
        super(JenkinsWrapperApi, self).__init__(jenkinsurl)
        self.job_loader_jenkins = jenkins.Jenkins(jenkinsurl, username, password)
        self.file_name = file_name
        self.func_name = func_name
        self.job_name_prefix = job_name_prefix
        self.reload_jobs = reload_jobs
        self.securitytoken = securitytoken
        WrapperJob._current_order = 1
        self._jf_jobs = OrderedDict()

    def _jenkins_job(self, name, exec_time, params, script, load_job=True, pre_delete=True):
        name = self.job_name_prefix + name
        assert not self._jf_jobs.get(name)
        # Create job in Jenkins
        if load_job:
            context = {'exec_time': exec_time, 'params': params or (), 'script': script, 'securitytoken': self.securitytoken}
            update_job_from_template(self.job_loader_jenkins, name, self.job_xml_template, pre_delete=pre_delete, context=context)
        return name

    def job(self, name, exec_time, max_fails, expect_invocations, expect_order, initial_buildno=0, invocation_delay=0.1, params=None, script=None):
        name = self._jenkins_job(name, exec_time, params, script, self.reload_jobs)
        self._jf_jobs[name] = (name, exec_time, max_fails, expect_invocations, expect_order)

    def flow_job(self, name=None, params=None):
        """
        Runs demo/test flow script as jenkins job
        Requires jenkinsflow to be copied to /tmp
        """
        if self.func_name:
            script  = "export PYTHONPATH=../..\n"
            script += "cd /tmp/jenkinsflow/test\n"
            script += "python -Bc &quot;from " + self.file_name.replace('.py', '') + " import *; test_" + self.func_name + "()&quot;"
            # script = "/tmp/jenkinsflow/test/test.py -s -p no:cache -p no:cov " + self.file_name + " -k  " + self.func_name
        else:
            script = "python " + jp('/tmp/jenkinsflow/demo', self.file_name)
        self._jenkins_job('0flow_' + name if name else '0flow', exec_time=0.5, params=params, script=script)

    # --- Wrapped API ---

    def delete_job(self, job_name):
        # del self._jf_jobs[job_name]
        self.job_loader_jenkins.delete_job(job_name)

    def create_job(self, job_name, config_xml):
        # assert job_name in self._jf_jobs
        self.job_loader_jenkins.create_job(job_name, config_xml)

    def get_job(self, name):
        try:
            job = self._jf_jobs[name]
            if isinstance(job, tuple):
                # super(JenkinsWrapperApi, self).poll()
                jenkins_job = super(JenkinsWrapperApi, self).get_job(name)
                self._jf_jobs[name] = job = WrapperJob(jenkins_job, job[0], job[1], job[2], job[3], job[4])
            return job
        except KeyError:
            raise jenkinsapi.custom_exceptions.UnknownJob(name)


def is_mocked():
    mocked = os.environ.get('JENKINSFLOW_MOCK_API')
    return mocked and mocked.lower() == 'true'


def api(file_name, jenkinsurl=os.environ.get('JENKINS_URL') or "http://localhost:8080", reload_jobs=True):
    base_name = os.path.basename(file_name).replace('.pyc', '.py')
    job_name_prefix = _file_name_subst.sub('', base_name)
    func_name = None
    if '_test' in file_name:
        func_name = sys._getframe().f_back.f_code.co_name  # pylint: disable=protected-access
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
    if is_mocked():
        print('Using Mocked API')
        clean_jobs_state()
        return MockApi(job_name_prefix)
    else:
        print('Using Real Jenkins API with wrapper')
        return JenkinsWrapperApi(file_name, func_name, job_name_prefix, reload_jobs,
                                 jenkinsurl, security.username, security.password, security.securitytoken)
