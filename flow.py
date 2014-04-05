# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

import os, time, re, abc, traceback
from os.path import join as jp
from collections import OrderedDict

from enum import Enum
from .ordered_enum import OrderedEnum
from .set_build_result import set_build_result


def mocked():
    mock_val = os.environ.get('JENKINSFLOW_MOCK_API')
    if mock_val is None:
        return False, 1.0

    try:
        return True, max(1.0, float(mock_val))
    except ValueError as ex:
        msg = "If JENKINSFLOW_MOCK_API is specied, the value must be set to the mock speedup, e.g. 2000 if you have a reasonably fast computer."
        msg += " If you experience FlowTimeoutException in tests, try lowering the value."
        raise ValueError(str(ex) + ". " + msg)


is_mocked, _hyperspeed_speedup = mocked()


def hyperspeed_time():
    return time.time() * _hyperspeed_speedup


# Note: Mock poll interval must be higher than the shortest exec_time (0.01) or some og the tests will break
_default_poll_interval = 0.5 if not is_mocked else 0.02
_default_report_interval = 5
_default_secret_params = '.*passw.*|.*PASSW.*'
_default_secret_params_re = re.compile(_default_secret_params)


class BuildResult(OrderedEnum):
    # pylint: disable=no-init
    FAILURE = 0
    UNSTABLE = 1
    SUCCESS = 2
    UNKNOWN = 3


class Propagation(OrderedEnum):
    # pylint: disable=no-init
    NORMAL = 0
    FAILURE_TO_UNSTABLE = 1
    UNCHECKED = 2


class Checking(OrderedEnum):
    # pylint: disable=no-init
    MUST_CHECK = 0
    HAS_UNCHECKED = 1
    FINISHED = 2


class Progress(Enum):
    # pylint: disable=no-init
    RUNNING = 1
    QUEUED = 2
    IDLE = 3


class JobControlException(Exception):
    def __init__(self, message, propagation=Propagation.NORMAL):
        super(JobControlException, self).__init__(message)
        self.propagation = propagation


class FlowTimeoutException(JobControlException):
    pass


class FlowScopeException(JobControlException):
    pass


class JobNotIdleException(JobControlException):
    pass


class JobControlFailException(JobControlException):
    __metaclass__ = abc.ABCMeta


class FailedSingleJobException(JobControlFailException):
    def __init__(self, job, propagation):
        msg = "Failed job: " + repr(job) + ", propagation:" + str(propagation)
        super(FailedSingleJobException, self).__init__(msg, propagation)


class MissingJobsException(FailedSingleJobException):
    def __init__(self, job_name):
        msg = "Could not get job info for: " + repr(job_name)
        super(MissingJobsException, self).__init__(msg, propagation=Propagation.NORMAL)


class FailedChildJobException(JobControlFailException):
    def __init__(self, flow_job, failed_child_job, propagation):
        msg = "Failed child job in: " + repr(flow_job) + ", child job:" + repr(failed_child_job) + ", propagation:" + str(propagation)
        super(FailedChildJobException, self).__init__(msg, propagation)


class FailedChildJobsException(JobControlFailException):
    def __init__(self, flow_job, failed_child_jobs, propagation):
        msg = "Failed child jobs in: " + repr(flow_job) + ", child jobs:" + repr(failed_child_jobs) + ", propagation:" + str(propagation)
        super(FailedChildJobsException, self).__init__(msg, propagation)


class _JobControl(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, parent_flow, securitytoken, max_tries, propagation, secret_params_re, allow_missing_jobs):
        self.parent_flow = parent_flow
        self.top_flow = parent_flow.top_flow

        self.max_tries = max_tries
        self.total_max_tries = self.max_tries * self.parent_flow.total_max_tries

        self.nesting_level = self.parent_flow.nesting_level + 1
        if self.nesting_level != self.top_flow.current_nesting_level + 1:
            raise FlowScopeException("Flow used out of scope")

        self.securitytoken = securitytoken or self.parent_flow.securitytoken
        self.propagation = propagation
        self.secret_params_re = secret_params_re or self.parent_flow.secret_params_re
        self.allow_missing_jobs = allow_missing_jobs if allow_missing_jobs is not None else self.parent_flow.allow_missing_jobs

        self.checking_status = Checking.MUST_CHECK
        self.result = BuildResult.UNKNOWN
        self.tried_times = 0
        self.total_tried_times = 0
        self.invocation_time = None

        self.node_id = self.top_flow.next_node_id
        self.top_flow.next_node_id += 1

    def __enter__(self):
        self.top_flow.current_nesting_level += 1

    def __exit__(self, exc_type, exc_value, traceback):
        self.top_flow.current_nesting_level -= 1

    @abc.abstractmethod
    def _prepare_first(self):
        """Must be called before the first invocation of a job"""

    def _prepare_to_invoke(self, reset_tried_times=False):
        """Must be called before each invocation of a job, as opposed to __init__, which is called once in entire run"""
        self.checking_status = Checking.MUST_CHECK if self.propagation != Propagation.UNCHECKED else Checking.HAS_UNCHECKED
        self.result = BuildResult.UNKNOWN
        self.tried_times = 1 if reset_tried_times else self.tried_times + 1
        self.total_tried_times += 1
        self.invocation_time = 0

    def _invoke_if_not_invoked(self):
        if self.invocation_time:
            return True

        self.invocation_time = hyperspeed_time()
        print("\nInvoking %s (%d/%d,%d/%d):" % (self.controller_type_name, self.tried_times, self.max_tries, self.total_tried_times, self.total_max_tries), self)
        return False

    @abc.abstractmethod
    def _check(self, report_now):
        """Polled by flow controller until the job reaches state 'successful' or tried_times == parent.max_tries * self.max_tries"""

    def _time_msg(self):
        now = hyperspeed_time()
        return "after: %.3fs/%.3fs" % (now - self.invocation_time, now - self.top_flow.start_time)

    @abc.abstractmethod
    def sequence(self):
        """'compact' representaion of flow/job 'name'"""

    @abc.abstractproperty
    def controller_type_name(self):
        """Short name for the type of flow/job"""

    @property
    def indentation(self):
        return self.nesting_level * 3 * ' '

    @property
    def api(self):
        return self.top_flow._api

    @property
    def propagate_result(self):
        if self.result == BuildResult.SUCCESS or self.propagation == Propagation.UNCHECKED:
            return BuildResult.SUCCESS
        if self.result == BuildResult.UNSTABLE or self.propagation == Propagation.FAILURE_TO_UNSTABLE:
            return BuildResult.UNSTABLE
        return BuildResult.FAILURE

    @property
    def propagate_checking_status(self):
        if self.propagation == Propagation.UNCHECKED:
            return max(Checking.HAS_UNCHECKED, self.checking_status)
        return self.checking_status

    @property
    def remaining_tries(self):
        return self.max_tries - self.tried_times

    @property
    def remaining_total_tries(self):
        return self.total_max_tries - self.total_tried_times

    def __repr__(self):
        return str(self.sequence())

    @abc.abstractmethod
    def last_jobs_in_flow(self):
        """For json graph calculation"""

    @abc.abstractmethod
    def nodes(self, node_to_id):
        """For json graph calculation"""

    @abc.abstractmethod
    def links(self, prev_jobs, node_to_id):
        """For json graph calculation"""


class _SingleJob(_JobControl):
    def __init__(self, parent_flow, securitytoken, job_name_prefix, max_tries, job_name, params, propagation, secret_params_re, allow_missing_jobs):
        for key, value in params.iteritems():
            # Handle parameters passed as int or bool. Booleans will be lowercased!
            if isinstance(value, (bool, int)):
                params[key] = str(value).lower()
        self.params = params
        super(_SingleJob, self).__init__(parent_flow, securitytoken, max_tries, propagation, secret_params_re, allow_missing_jobs)
        # There is no separate retry for individual jobs, so set self.total_max_tries to the same as parent flow!
        self.total_max_tries = self.parent_flow.total_max_tries
        self.job = None
        self.old_build_num = None
        self.name = job_name_prefix + job_name
        self.repr_str = self.name
        self.jenkins_baseurl = None

        print(self.indentation + "job: ", self.name)

    def _prepare_first(self, require_job=False):
        try:
            if require_job:
                if hasattr(self.api, 'job_poll'):
                    self.api.poll_job(self.name)
                else:
                    self.api.poll()
            self.job = self.api.get_job(self.name)
        except Exception as ex:
            # TODO? stack trace
            self.repr_str = repr(ex)
            if require_job or not self.allow_missing_jobs:
                self.checking_status = Checking.FINISHED
                self.result = BuildResult.FAILURE
                raise MissingJobsException(self.name)
            print(self.indentation + "NOTE: ", self.repr_str)
            super(_SingleJob, self)._prepare_to_invoke(reset_tried_times=False)
            return

        self._prepare_to_invoke()
        pgstat = self.progress_status()
        if self.top_flow.require_idle and pgstat != Progress.IDLE:
            # Pylint does not like Enum pylint: disable=no-member
            raise JobNotIdleException("Job: " + self.name + " is in state " + pgstat.name + ". It must be " + Progress.IDLE.name + '.')

        # Build repr string with build-url with secret params replaced by '***'
        url = self.job.get_build_triggerurl()
        # jenkinsapi returns basic path without any args
        # Insert ' - ' so that the build URL is not directly clickable, but will instead point to the job
        part1 = url.replace(self.job.name, self.job.name + ' - ')
        query = [key + '=' + (value if not self.secret_params_re.search(key) else '******') for key, value in self.params.iteritems()]
        self.repr_str = part1 + ('?' + '&'.join(query) if query else '')

        print(self.indentation + "job: ", end='')
        self._print_status_message(self.old_build_num)
        if self.top_flow.direct_url:
            self.jenkins_baseurl = self.job.baseurl.replace('/job/' + self.name, '')

    def __repr__(self):
        return self.repr_str

    def progress_status(self):
        return Progress.RUNNING if self.job.is_running() else Progress.QUEUED if self.job.is_queued() else Progress.IDLE

    def _print_status_message(self, build_num):
        print(repr(self.job.name), "Status", self.progress_status().name, "- latest build:", '#' + str(build_num) if build_num else None)

    def _prepare_to_invoke(self, reset_tried_times=False):
        super(_SingleJob, self)._prepare_to_invoke(reset_tried_times)
        self.job.poll()
        old_build = self.job.get_last_build_or_none()
        self.old_build_num = old_build.buildno if old_build else None

    def _check(self, report_now):
        if self.job is None:
            self._prepare_first(require_job=True)

        if not self._invoke_if_not_invoked():
            # Don't re-invoke unchecked jobs that are still running
            if self.propagation != Propagation.UNCHECKED or not self.job.is_running():
                build_params = self.params if self.params else None
                if self.top_flow.direct_url:
                    self.job.baseurl = self.top_flow.direct_url + '/job/' + self.name
                self.job.invoke(securitytoken=self.securitytoken, invoke_pre_check_delay=0, block=False, build_params=build_params, cause=self.top_flow.cause)

        for ii in range(1, 20):
            try:
                self.job.poll()
                build = self.job.get_last_build_or_none()
                break
            except KeyError as ex:  # pragma: no cover
                # Workaround for jenkinsapi timing dependency?
                if ii == 1:
                    print("poll or get_last_build_or_none' failed: " + str(ex) + ", retrying.")
                    traceback.print_exc()
                time.sleep(0.1 / _hyperspeed_speedup)

        if build is None or build.buildno == self.old_build_num or build.is_running():
            if report_now:
                self._print_status_message(build.buildno if build else self.old_build_num)
            return

        # The job has stopped running
        print ("job", self, "stopped running")
        self.checking_status = Checking.FINISHED
        self._print_status_message(build.buildno)
        self.result = BuildResult[build.get_status()]
        url = build.get_result_url().replace('testReport/api/python', 'console').replace('testReport/api/json', 'console')
        if self.top_flow.direct_url:
            url = url.replace(self.top_flow.direct_url, self.jenkins_baseurl)
        print(str(build.get_status()) + ":", repr(self.job.name), "- build:", url, self._time_msg())

        if self.result == BuildResult.FAILURE:
            raise FailedSingleJobException(self.job, self.propagation)

    def sequence(self):
        return self.name

    @property
    def controller_type_name(self):
        return "Job"

    def last_jobs_in_flow(self):
        return [self] if self.propagation != Propagation.UNCHECKED else []

    def nodes(self, node_to_id):
        node_name = self.name[self.top_flow.json_strip_index:]
        url = self.job.baseurl if self.job is not None else None
        return [OrderedDict((("id", node_to_id(self)), ("name", node_name), ("url", url)))]

    def links(self, prev_jobs, node_to_id):
        return [OrderedDict((("source", node_to_id(job)), ("target", node_to_id(self)))) for job in prev_jobs]


# Retries are handled in the _Flow classes instead of _SingleJob since the individual jobs don't know
# how to retry. The _Serial flow is retried from start of flow and in _Parallel flow individual jobs
# are retried immediately

class _Flow(_JobControl):
    __metaclass__ = abc.ABCMeta

    def __init__(self, parent_flow, timeout, securitytoken, job_name_prefix, max_tries, propagation, report_interval, secret_params, allow_missing_jobs):
        secret_params_re = re.compile(secret_params) if isinstance(secret_params, str) else secret_params
        super(_Flow, self).__init__(parent_flow, securitytoken, max_tries, propagation, secret_params_re, allow_missing_jobs)
        self.timeout = timeout
        self.job_name_prefix = self.parent_flow.job_name_prefix + job_name_prefix
        self.report_interval = report_interval or self.parent_flow.report_interval

        self.jobs = []
        self.last_report_time = 0
        self._failed_child_jobs = {}

    def parallel(self, timeout=0, securitytoken=None, job_name_prefix='', max_tries=1, propagation=Propagation.NORMAL, report_interval=None, secret_params=None, allow_missing_jobs=None):
        return _Parallel(self, timeout, securitytoken, job_name_prefix, max_tries, propagation, report_interval, secret_params, allow_missing_jobs)

    def serial(self, timeout=0, securitytoken=None, job_name_prefix='', max_tries=1, propagation=Propagation.NORMAL, report_interval=None, secret_params=None, allow_missing_jobs=None):
        assert isinstance(propagation, Propagation)
        return _Serial(self, timeout, securitytoken, job_name_prefix, max_tries, propagation, report_interval, secret_params, allow_missing_jobs)

    def invoke(self, job_name, **params):
        job = _SingleJob(self, self.securitytoken, self.job_name_prefix, self.max_tries, job_name, params, self.propagation, self.secret_params_re, self.allow_missing_jobs)
        self.jobs.append(job)

    def invoke_unchecked(self, job_name, **params):
        job = _SingleJob(self, self.securitytoken, self.job_name_prefix, self.max_tries, job_name, params, Propagation.UNCHECKED, self.secret_params_re, self.allow_missing_jobs)
        self.jobs.append(job)

    @property
    def controller_type_name(self):
        return "Flow"

    def _check_timeout(self):
        now = hyperspeed_time()
        if self.timeout and now - self.invocation_time > self.timeout:
            unfinished_msg = ". Unfinished jobs:" + repr([repr(job) for job in self.jobs if job.checking_status == Checking.MUST_CHECK])
            raise FlowTimeoutException("Timeout " + self._time_msg() + ", in flow " + str(self) + unfinished_msg, self.propagation)

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type:
            return None

        super(_Flow, self).__exit__(exc_type, exc_value, traceback)
        if self.parent_flow:
            # Insert myself in parent if I'm not empty
            if self.jobs:
                self.parent_flow.jobs.append(self)
                return

            print(self.indentation + "INFO: Ignoring empty flow")

    def _check_invoke_report(self):
        self._invoke_if_not_invoked()

        now = hyperspeed_time()
        report_now = now - self.last_report_time >= self.report_interval
        if report_now:
            self.last_report_time = now
        return report_now

    def report_result(self):
        # Pylint does not like Enum pylint: disable=no-member
        print(self.result.name, self, self._time_msg())

    def json(self, file_path, indent=None):
        node_to_id = lambda job: job.node_id
        if indent:
            node_to_id = lambda job: job.name

        nodes = self.nodes(node_to_id)
        links = self.links([], node_to_id)
        graph = {'nodes': nodes, 'links': links}

        import json
        from atomicfile import AtomicFile
        if file_path is not None:
            with AtomicFile(file_path, 'w+') as out_file:
                json.dump(graph, out_file, indent=indent)
        else:
            return json.dumps(graph, indent=indent)


class _Parallel(_Flow):
    def _prepare_first(self):
        print(self.indentation + "parallel flow: (")
        self._prepare_to_invoke()
        for job in self.jobs:
            job._prepare_first()
        print(self.indentation + ")\n")

    def __enter__(self):
        print(self.indentation + "parallel flow: (")
        super(_Parallel, self).__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        print(self.indentation + ")")
        super(_Parallel, self).__exit__(exc_type, exc_value, traceback)
        print()

    def _check(self, report_now):
        report_now = self._check_invoke_report()

        self.checking_status = Checking.FINISHED
        for job in self.jobs:
            try:
                if job.checking_status != Checking.FINISHED:
                    job._check(report_now)
                    self.checking_status = min(self.checking_status, job.propagate_checking_status)
                    if id(job) in self._failed_child_jobs:
                        del self._failed_child_jobs[id(job)]
            except JobControlFailException:
                self._failed_child_jobs[id(job)] = job

                if job.remaining_tries:
                    print("RETRY:", job, "failed but will be retried. Up to", job.remaining_tries, "more times in current flow")
                    self.checking_status = Checking.MUST_CHECK
                    job._prepare_to_invoke()
                    continue

                if job.remaining_total_tries:
                    print("RETRY:", job, "failed but will be retried. Up to", job.remaining_total_tries, "more times through outer flow")
                    job._prepare_to_invoke(reset_tried_times=True)
                    continue

                job.checking_status = Checking.FINISHED

        if self.checking_status != Checking.MUST_CHECK and self.result == BuildResult.UNKNOWN:
            # All jobs have stopped running or are 'unchecked'
            for job in self.jobs:
                self.result = min(self.result, job.propagate_result)
            self.report_result()

            if self.result == BuildResult.FAILURE:
                raise FailedChildJobsException(self, self._failed_child_jobs.values(), self.propagation)
        else:
            self._check_timeout()

    def sequence(self):
        return tuple([job.sequence() for job in self.jobs])

    def last_jobs_in_flow(self):
        jobs = []
        for job in self.jobs:
            jobs.extend(job.last_jobs_in_flow())
        return jobs

    def nodes(self, node_to_id):
        nodes = []
        for job in self.jobs:
            child_nodes = job.nodes(node_to_id)
            nodes.extend(child_nodes)
        return nodes

    def links(self, prev_jobs, node_to_id):
        links = []
        for job in self.jobs:
            child_links = job.links(prev_jobs, node_to_id)
            links.extend(child_links)
        return links


class _Serial(_Flow):
    def __init__(self, parent_flow, securitytoken, timeout, job_name_prefix='', max_tries=1, propagation=Propagation.NORMAL,
                 report_interval=None, secret_params=_default_secret_params_re, allow_missing_jobs=None):
        super(_Serial, self).__init__(parent_flow, securitytoken, timeout, job_name_prefix, max_tries, propagation,
                                      report_interval, secret_params, allow_missing_jobs)
        self.job_index = 0

    def _prepare_first(self):
        print(self.indentation + "serial flow: [")
        self._prepare_to_invoke()
        for job in self.jobs:
            job._prepare_first()
        print(self.indentation + "]\n")

    def _prepare_to_invoke(self, reset_tried_times=False):
        super(_Serial, self)._prepare_to_invoke(reset_tried_times)
        self.job_index = 0

    def __enter__(self):
        print(self.indentation + "serial flow: [")
        super(_Serial, self).__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        print(self.indentation + "]")
        super(_Serial, self).__exit__(exc_type, exc_value, traceback)
        print()

    def _check(self, report_now):
        report_now = self._check_invoke_report()

        self.checking_status = Checking.FINISHED
        for job in self.jobs[0:self.job_index + 1]:
            try:
                if job.checking_status != Checking.FINISHED:
                    job._check(report_now)
                    self.checking_status = min(self.checking_status, job.propagate_checking_status)
            except JobControlFailException:
                # The job has stopped running
                if job.remaining_tries:
                    if job.propagation != Propagation.NORMAL:
                        print("MAY RETRY:", job, job.propagation, " failed, will only retry if checked failures. Up to", job.remaining_tries, "more times in current flow")
                        continue
                    print("RETRY:", job, "failed, retrying child jobs from beginning. Up to", job.remaining_tries, "more times in current flow")
                    self.checking_status = Checking.MUST_CHECK
                    for pre_job in self.jobs[0:self.job_index + 1]:
                        pre_job._prepare_to_invoke()
                    self.job_index = 0
                    continue

                if job.remaining_total_tries:
                    if job.propagation != Propagation.NORMAL:
                        print("MAY RETRY:", job, job.propagation, " failed, will only retry if checked failures. Up to", job.remaining_total_tries, "more times through outer flow")
                        continue
                    print("RETRY:", job, "failed, retrying child jobs from beginning. Up to", job.remaining_total_tries, "more times through outer flow")
                    for pre_job in self.jobs[0:self.job_index + 1]:
                        pre_job._prepare_to_invoke(reset_tried_times=True)
                    self.job_index = 0
                    continue

                job.checking_status = Checking.FINISHED
                if job.propagation != Propagation.UNCHECKED:
                    self.job_index = len(self.jobs)

        if self.checking_status != Checking.MUST_CHECK and self.result == BuildResult.UNKNOWN:
            for job in self.jobs[0:self.job_index + 1]:
                self.result = min(self.result, job.propagate_result)

            if self.result == BuildResult.FAILURE:
                self.report_result()
                raise FailedChildJobException(self, job, self.propagation)

            self.job_index += 1
            if self.job_index < len(self.jobs):
                self.checking_status = Checking.MUST_CHECK
                self.result = BuildResult.UNKNOWN
                return

            # All jobs have stopped running or are 'unchecked'
            self.report_result()
        else:
            self._check_timeout()

    def sequence(self):
        return [job.sequence() for job in self.jobs]

    def last_jobs_in_flow(self):
        for job in self.jobs[-1:0:-1]:
            last_jobs = job.last_jobs_in_flow()
            if last_jobs:
                return last_jobs
        return []

    def nodes(self, node_to_id):
        nodes = []
        for job in self.jobs:
            child_nodes = job.nodes(node_to_id)
            nodes.extend(child_nodes)
        return nodes

    def links(self, prev_jobs, node_to_id):
        links = []
        for job in self.jobs:
            child_links = job.links(prev_jobs, node_to_id)
            links.extend(child_links)
            prev_jobs = job.last_jobs_in_flow()
        return links


class _TopLevelControllerMixin(object):
    __metaclass__ = abc.ABCMeta

    def toplevel_init(self, jenkins_api, securitytoken, username, password, top_level_job_name_prefix, poll_interval, direct_url, require_idle,
                      json_dir, json_indent, json_strip_top_level_prefix):
        self._start_msg()
        # pylint: disable=attribute-defined-outside-init
        # Note: Special handling in top level flow, these atributes will be modified in proper flow init
        self.parent_flow = self
        self.top_flow = self
        self.job_name_prefix = ''
        self.total_max_tries = 1
        self.nesting_level = -1
        self.current_nesting_level = -1
        self.report_interval = _default_report_interval
        self.secret_params_re = _default_secret_params_re
        self.allow_missing_jobs = None
        self.next_node_id = 0

        jenkins_job_name = os.environ.get('JOB_NAME')
        if jenkins_job_name:
            self.cause = "By flow job " + repr(jenkins_job_name) + ' #' +  os.environ.get('BUILD_NUMBER', ' None')
        else:
            import getpass
            user = getpass.getuser()
            self.cause = "By flow script, user " + repr(user)

        self._api = jenkins_api
        self.securitytoken = securitytoken
        self.username = username
        self.password = password
        self.poll_interval = poll_interval
        self.direct_url = direct_url.rstrip('/') if direct_url is not None else direct_url
        self.require_idle = require_idle

        self.json_dir = json_dir
        self.json_indent = json_indent
        self.json_strip_index = len(top_level_job_name_prefix) if json_strip_top_level_prefix else 0
        self.json_file = jp(self.json_dir, 'flow_graph.json') if json_dir is not None else None

        # Allow test framework to set securitytoken, so that we won't have to litter all the testcases with it
        return self.securitytoken or jenkins_api.securitytoken if hasattr(jenkins_api, 'securitytoken') else None

    @staticmethod
    def _start_msg():
        print()
        print("=== Jenkinsflow ===")
        print()
        print("Legend:")
        print("Serial builds: []")
        print("Parallel builds: ()")
        print("Invoking (w/x,y/z): w=current invocation in current flow scope, x=max in scope, y=total number of invocations, z=total max invocations")
        print("Elapsed time: 'after: x/y': x=time spent during current run of job, y=time elapsed since start of outermost flow")
        print()
        print("--- Calculating flow graph ---")

    def wait_for_jobs(self):
        if not self.jobs:
            print("WARNING: Empty toplevel flow", self, "nothing to do.")
            return

        if self.json_dir:
            self.json(jp(self.json_dir, 'flow_graph.json'), self.json_indent)

        # Wait for jobs to finish
        print()
        print("--- Getting initial job status ---")
        self.api.poll()
        self._prepare_first()

        if self.json_file:
            self.json(self.json_file, self.json_indent)

        # pylint: disable=attribute-defined-outside-init
        self.start_time = hyperspeed_time()
        self.last_report_time = self.start_time

        print()
        print("--- Starting flow ---")
        sleep_time = min(self.poll_interval, self.report_interval) / _hyperspeed_speedup
        while self.checking_status == Checking.MUST_CHECK:
            if hasattr(self.api, 'quick_poll'):
                self.api.quick_poll()
            self._check(None)
            time.sleep(sleep_time)

        if self.result == BuildResult.UNSTABLE:
            set_build_result(self.username, self.password, 'unstable', direct_url=self.top_flow.direct_url)


class parallel(_Parallel, _TopLevelControllerMixin):
    def __init__(self, jenkins_api, timeout, securitytoken=None, username=None, password=None, job_name_prefix='', max_tries=1, propagation=Propagation.NORMAL,
                 report_interval=_default_report_interval, poll_interval=_default_poll_interval, secret_params=_default_secret_params_re, allow_missing_jobs=False,
                 json_dir=None, json_indent=None, json_strip_top_level_prefix=True, direct_url=None, require_idle=True):
        """propagation: causes failure in this job not to fail the parent flow"""
        assert isinstance(propagation, Propagation)
        securitytoken = self.toplevel_init(jenkins_api, securitytoken, username, password, job_name_prefix, poll_interval, direct_url, require_idle,
                                           json_dir, json_indent, json_strip_top_level_prefix)
        super(parallel, self).__init__(self, timeout, securitytoken, job_name_prefix, max_tries, propagation, report_interval, secret_params, allow_missing_jobs)
        self.parent_flow = None

    def __exit__(self, exc_type, exc_value, traceback):
        super(parallel, self).__exit__(exc_type, exc_value, traceback)
        self.wait_for_jobs()


class serial(_Serial, _TopLevelControllerMixin):
    def __init__(self, jenkins_api, timeout, securitytoken=None, username=None, password=None, job_name_prefix='', max_tries=1, propagation=Propagation.NORMAL,
                 report_interval=_default_report_interval, poll_interval=_default_poll_interval, secret_params=_default_secret_params_re, allow_missing_jobs=False,
                 json_dir=None, json_indent=None, json_strip_top_level_prefix=True, direct_url=None, require_idle=True):
        """propagation: causes failure in this job not to fail the parent flow"""
        assert isinstance(propagation, Propagation)
        securitytoken = self.toplevel_init(jenkins_api, securitytoken, username, password, job_name_prefix, poll_interval, direct_url, require_idle,
                                           json_dir, json_indent, json_strip_top_level_prefix)
        super(serial, self).__init__(self, timeout, securitytoken, job_name_prefix, max_tries, propagation, report_interval, secret_params, allow_missing_jobs)
        self.parent_flow = None

    def __exit__(self, exc_type, exc_value, traceback):
        super(serial, self).__exit__(exc_type, exc_value, traceback)
        self.wait_for_jobs()
