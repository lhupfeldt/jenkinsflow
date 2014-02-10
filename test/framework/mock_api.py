import os, sys, abc, re
from collections import OrderedDict
import time
from os.path import join as jp

here = os.path.abspath(os.path.dirname(__file__))
sys.path.append(jp(here, '../..'))

from jenkinsflow.jobload import update_job
from jenkinsapi import jenkins

from clean_jobs_state import clean_jobs_state
from jobloadtemplate import update_job_from_template

_current_order = 1


class Job(object):
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
        # print "Mock job: ", what, self, "time:", time.time()
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

    def invoke(self, securitytoken, invoke_pre_check_delay, block, build_params):
        global _current_order
        self.just_invoked = True
        self.actual_order = _current_order
        _current_order += 1
        self.invocation += 1
        self.invocation_time = time.time()
        self.start_time = self.invocation_time + self.invocation_delay
        self.end_time = self.start_time + self.exec_time
        self.debug('invoke')

    def __repr__(self):
        return self.name + \
            ", expect_invocations: " + repr(self.expect_invocations) + \
            ", invocation: " + repr(self.invocation) + \
            ", expect_order: " + repr(self.expect_order) + \
            ", start_time: " + repr(self.start_time) + \
            ", exec_time: " + repr(self.exec_time) + \
            ", end_time: " + repr(self.end_time)


class Build(object):
    def __init__(self, job, initial_buildno):
        self.job = job
        self.buildno = initial_buildno
        self.debug('__init__')

    def debug(self, what):
        print "Mock build: ", what, self, "time:", time.time()

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

    def mock_job(self, name, exec_time, max_fails, expect_invocations, expect_order, initial_buildno=0, invocation_delay=0.1, job_xml_template=None, params=None):
        name = self.job_name_prefix + name
        assert not self._jf_jobs.get(name)
        if is_mocked():
            self._jf_jobs[name] = Job(name, exec_time, max_fails, expect_invocations, expect_order, initial_buildno, invocation_delay)
        elif job_xml_template or params:
            if params:
                assert job_xml_template, "Default job.xml does not support special 'params', you must specify a template"
            update_job_from_template(self, name, job_xml_template, pre_delete=True, params=params, exec_time=exec_time)
        else:
            update_job(self, name, self.config_xml, pre_delete=True)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if not exc_type:
            self.test_results()

    def test_results(self):
        pass


class MockApi(_JobsMixin):
    def __init__(self, job_name_prefix):
        self.job_name_prefix = job_name_prefix
        self._jf_jobs = OrderedDict()

    # --- Mock API ---

    def get_job(self, name):
        return self._jf_jobs[name]

    def test_results(self):
        print "Checking results"

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
            assert job.expect_invocations == job.invocation, "Job: " + job.name + " invoked " + job.invocation + " times, expected " + job.expect_invocations + " invocations"
            if job.invocation > job.max_fails:
                assert job.get_last_build_or_none().is_good(), "Job: " + job.name + " should have been in state good, but it is not"
            elif job.expect_invocations != 0:
                assert not job.get_last_build_or_none().is_good(), "Job: " + job.name + " should have been in failed state, but it is not"


class JenkinsWrapper(jenkins.Jenkins, _JobsMixin):
    def __init__(self, job_name_prefix, jenkinsurl):
        super(JenkinsWrapper, self).__init__(jenkinsurl)
        self.job_name_prefix = job_name_prefix
        self._jf_jobs = OrderedDict()
        try:
            file_name = jp(here, self.job_name_prefix + 'job.xml')
            with open(file_name) as ff:
                print "Using specialized job xml:", file_name
                self.config_xml = ff.read()
        except IOError:
            with open(jp(here, 'job.xml')) as ff:
                self.config_xml = ff.read()


def is_mocked():
    mocked = os.environ.get('JENKINSFLOW_MOCK_API')
    return mocked and mocked.lower() == 'true'


def api(job_name_prefix, jenkinsurl=os.environ.get('JENKINSFLOW_JENKINSURL') or "http://localhost:8080"):
    job_name_prefix = re.sub(r'(_jobs)?\.pyc?$', '_', os.path.basename(job_name_prefix))
    if is_mocked():
        print 'Using Mocked API'
        clean_jobs_state()
        return MockApi(job_name_prefix)
    else:
        print 'Using Real Jenkins API'
        return JenkinsWrapper(job_name_prefix, jenkinsurl)
