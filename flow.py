# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

import os, re, abc
from os.path import join as jp
from collections import OrderedDict
from itertools import chain

from enum import Enum
from .ordered_enum import OrderedEnum
from .set_build_result import set_build_result
from .specialized_api import UnknownJobException
from .mocked import hyperspeed, mocked


_default_poll_interval = 0.5 if not mocked else 0.001
_default_report_interval = 5
_default_secret_params = '.*passw.*|.*PASSW.*'
_default_secret_params_re = re.compile(_default_secret_params)


class BuildResult(OrderedEnum):
    # pylint: disable=no-init
    FAILURE = 0
    ABORTED = 1
    UNSTABLE = 2
    SUCCESS = 3
    UNKNOWN = 4

_build_result_failures = (BuildResult.FAILURE, BuildResult.ABORTED)


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


class MessageRedefinedException(JobControlException):
    pass


class JobControlFailException(JobControlException):
    __metaclass__ = abc.ABCMeta


class FailedSingleJobException(JobControlFailException):
    def __init__(self, job, propagation):
        msg = "Failed job: " + repr(job) + ", propagation:" + str(propagation)
        super(FailedSingleJobException, self).__init__(msg, propagation)


class MissingJobsException(JobControlFailException):
    def __init__(self, ex):
        super(MissingJobsException, self).__init__(ex.message, propagation=Propagation.NORMAL)


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
        self.msg = None

        self.node_id = self.top_flow.next_node_id
        self.top_flow.next_node_id += 1

    def __enter__(self):
        self.top_flow.current_nesting_level += 1
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.top_flow.current_nesting_level -= 1

    @abc.abstractmethod
    def _prepare_first(self):
        """Must be called before the first invocation of a job"""

    def _prepare_to_invoke(self, reset_tried_times=False):
        """Must be called before each invocation of a job, as opposed to _prepare_first, which is called once in entire run"""
        self.checking_status = Checking.MUST_CHECK if self.propagation != Propagation.UNCHECKED else Checking.HAS_UNCHECKED
        self.result = BuildResult.UNKNOWN
        self.tried_times = 1 if reset_tried_times else self.tried_times + 1
        self.total_tried_times += 1
        self.invocation_time = 0

    def _invocation_message(self, controller_type_name, invocation_repr):
        if self.msg is not None:
            print(self.msg)
        print("\nInvoking %s (%d/%d,%d/%d):" % (controller_type_name, self.tried_times, self.max_tries, self.total_tried_times, self.total_max_tries), invocation_repr)

    def _must_invoke_set_invocation_time(self):
        if self.invocation_time:
            return False

        self.invocation_time = hyperspeed.time()
        return True

    @abc.abstractmethod
    def _check(self, report_now):
        """Polled by flow controller until the job reaches state 'successful' or tried_times == parent.max_tries * self.max_tries"""

    def _time_msg(self):
        now = hyperspeed.time()
        return "after: %.3fs/%.3fs" % (now - self.invocation_time, now - self.top_flow.start_time)

    @abc.abstractmethod
    def sequence(self):
        """'compact' representaion of flow/job 'name'"""

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

    def message(self, msg):
        """Define a message that will be printed before the invocation of the job or flow on which it is defined.

        Args:
            msg (object): The message that will be printed.
        """

        if self.msg is not None:
            raise MessageRedefinedException("Existing message: " + repr(self.msg) + ", new message: " + repr(msg))
        self.msg = msg

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
        self.repr_str = ("unchecked " if self.propagation == Propagation.UNCHECKED else "") + "job: " + repr(self.name)
        self.jenkins_baseurl = None

        print(self.indentation + repr(self))

    def _prepare_first(self, require_job=False):
        try:
            self.job = self.api.get_job(self.name)
        except UnknownJobException as ex:
            # TODO? stack trace
            if require_job or not self.allow_missing_jobs:
                self.checking_status = Checking.FINISHED
                self.result = BuildResult.FAILURE
                raise MissingJobsException(ex)
            print(self.indentation + repr(self), " - MISSING JOB")
            super(_SingleJob, self)._prepare_to_invoke(reset_tried_times=False)
            return

        self._prepare_to_invoke()
        pgstat = self.progress_status()
        if self.top_flow.require_idle and pgstat != Progress.IDLE:
            # Pylint does not like Enum pylint: disable=no-member
            raise JobNotIdleException(repr(self) + " is in state " + pgstat.name + ". It must be " + Progress.IDLE.name + '.')

        print(self.indentation + self._status_message(self.old_build_num))

    def _show_job_definition(self):
        first = current = OrderedDict()
        last = OrderedDict()

        display_params = dict((key, (value if not self.secret_params_re.search(key) else '******')) for key, value in self.params.iteritems())
        for name in self.top_flow.params_display_order:
            if name == '*':
                current = last
            if name in display_params:
                current[name] = display_params[name]
                del display_params[name]

        if self.job:
            print('Defined Job', self.job.public_uri + (' - parameters:' if display_params else ''))
        else:
            print('Defined Job', repr(self.name) + " - MISSING JOB")
        for key, value in chain(first.iteritems(), sorted(display_params.iteritems()), last.iteritems()):
            print("    ", key, '=', repr(value))
        if self.params:
            print("")

    def __repr__(self):
        return self.repr_str

    def progress_status(self):
        return Progress.RUNNING if self.job.is_running() else Progress.QUEUED if self.job.is_queued() else Progress.IDLE

    def _status_message(self, build_num):
        return repr(self) + " Status " + self.progress_status().name + " - latest build: " + '#' + str(build_num if build_num else None)

    def _prepare_to_invoke(self, reset_tried_times=False):
        super(_SingleJob, self)._prepare_to_invoke(reset_tried_times)
        self.job.poll()
        old_build = self.job.get_last_build_or_none()
        self.old_build_num = old_build.buildno if old_build else None

    def _check(self, report_now):
        if self.job is None:
            self._prepare_first(require_job=True)

        if self._must_invoke_set_invocation_time():
            # Don't re-invoke unchecked jobs that are still running
            if self.propagation != Propagation.UNCHECKED or not self.job.is_running():
                self._invocation_message('Job', self.job.console_url(self.old_build_num + 1 if self.old_build_num else 1))
                self.job.invoke(securitytoken=self.securitytoken, build_params=self.params if self.params else None, cause=self.top_flow.cause)

        build = self.job.get_last_build_or_none()
        if build is None or build.buildno == self.old_build_num or build.is_running():
            if report_now:
                print(self._status_message(build.buildno if build else self.old_build_num))
            return

        # The job has stopped running
        print(self, "stopped running")
        self.checking_status = Checking.FINISHED
        print(self._status_message(build.buildno))
        self.result = BuildResult[build.get_status()]
        # Pylint does not like Enum pylint: disable=no-member
        unchecked = (Propagation.UNCHECKED.name + ' ') if self.propagation == Propagation.UNCHECKED else ''
        print(unchecked + str(build.get_status()) + ":", repr(self.job.name), "- build:", build.console_url(), self._time_msg())

        if self.result in _build_result_failures:
            raise FailedSingleJobException(self.job, self.propagation)

    def sequence(self):
        return self.name

    def _final_status(self):
        if self.job is not None:
            # Pylint does not like Enum pylint: disable=maybe-no-member
            if self.result == BuildResult.SUCCESS:
                print(self.indentation + repr(self), self.result.name)
                return

            progress = ""
            if self.progress_status() != Progress.IDLE:
                progress = "- " + self.progress_status().name
            console_url = ""
            if self.result != BuildResult.UNKNOWN:
                console_url = self.job.console_url(self.old_build_num + 1 if self.old_build_num else 1)
            print(self.indentation + repr(self), self.result.name, progress, console_url)
            return

        print(self.indentation + repr(self), " - MISSING JOB")

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
    _enter_str = None
    _exit_str = None

    def __init__(self, parent_flow, timeout, securitytoken, job_name_prefix, max_tries, propagation, report_interval, secret_params, allow_missing_jobs):
        secret_params_re = re.compile(secret_params) if isinstance(secret_params, str) else secret_params
        super(_Flow, self).__init__(parent_flow, securitytoken, max_tries, propagation, secret_params_re, allow_missing_jobs)
        self.timeout = timeout
        self.job_name_prefix = self.parent_flow.job_name_prefix + job_name_prefix if job_name_prefix is not None else ""
        self.report_interval = report_interval or self.parent_flow.report_interval

        self.jobs = []
        self.last_report_time = 0
        self._failed_child_jobs = {}

    def parallel(self, timeout=0, securitytoken=None, job_name_prefix='', max_tries=1, propagation=Propagation.NORMAL, report_interval=None, secret_params=None, allow_missing_jobs=None):
        """Defines a parallel flow where nested jobs or flows are executed simultaneously.

        Only differences to :py:meth:`.serial` are described.

        Args:
            max_tries (int): Maximum number of times to invoke the jobs in the flow. Default is 1, meaning no retry will be attempted in case jobs fails.
                If a job fails it is immediately retried::

                    with parallel(..., max_tries=3) as sf:
                        sf.invoke('a', ...)
                        sf.invoke('b', ...)  # fail -> restart job 'b'
                        sf.invoke('c', ...)

        Returns:
            parallel flow object
        """

        assert isinstance(propagation, Propagation)
        return _Parallel(self, timeout, securitytoken, job_name_prefix, max_tries, propagation, report_interval, secret_params, allow_missing_jobs)

    def serial(self, timeout=0, securitytoken=None, job_name_prefix='', max_tries=1, propagation=Propagation.NORMAL, report_interval=None, secret_params=None, allow_missing_jobs=None):
        """Defines a serial flow where nested jobs or flows are executed in order.

        Args:
            timeout (float): Maximum time in seconds to wait for flow jobs to finish. 0 means infinite, however, this flow can not run longer than the minimum timeout of any parent flows.
                Note that jenkins jobs are NOT terminated when the flow times out.
            securitytoken (str): Token to use on security enabled Jenkins instead of username/password. The Jenkins job must have the token configured.
                If None, the parent flow securitytoken is used.
            job_name_prefix (str): All jobs defined in flow will automatically be prefixed with the parent flow job_name_prefix + this job_name_prefix before invoking Jenkins job.
            max_tries (int): Maximum number of times to invoke the flow. Default is 1, meaning no retry will be attempted in case a job fails.
                If a job fails, jobs are retried from start of the parallel flow::

                    with serial(..., max_tries=3) as sf:
                        sf.invoke('a', ...)
                        sf.invoke('b', ...)  # fail -> restart flow from job 'a'
                        sf.invoke('c', ...)

                Retries may be nested::

                    with parallel(..., max_tries=2) as sf:
                        with sf.serial(..., max_tries=3) as sf:
                            sf.invoke('a', ...)  # If a fails it could be invoked up to 6 times

            propagation (Propagation): How to propagate errors from failed Jenkins jobs. This will not change the result of the failed job itself,
                but only the result of the Jenkins job running the flow (if it is being run from a Jenkins job).
            report_interval (float): The interval in seconds between reporting the status of polled Jenkins jobs.
                If None the parent flow report_interval is used.
            secret_params (re.RegexObject): Regex of Jenkins job invocation parameter names, for which the value will be masked out with '******' when parameters are printed.
                If None the parent flow secret_params is used.
            allow_missing_jobs (boolean): If true it is not considered an error if Jenkins jobs are missing when the flow starts.
                It is assumed that the missing jobs are created by jobs in the flow, prior to the missing jobs being invoked.
                If None the parent flow allow_missing_jobs is used.

        Returns:
            serial flow object

        Raises:
            JobControlException
        """

        assert isinstance(propagation, Propagation)
        return _Serial(self, timeout, securitytoken, job_name_prefix, max_tries, propagation, report_interval, secret_params, allow_missing_jobs)

    def invoke(self, job_name, **params):
        """Define a Jenkins job that will be invoked under control of the surrounding flow.
        
        This does not create the job in Jenkins. It defines how the job will be invoked by ``jenkinsflow``.

        Args:
            job_name (str): The last part of the name of the job in jenkins.
                If the surrounding flow sets the :py:obj:`job_name_prefix` the actual name of the invoked job will be the parent flow job_name_prefix + job_name.
            **params (str, int, boolean): Arguments passed to Jenkins when invoking the job. Strings are passed as they are,
                booleans are automatically converted to strings and lowercased, integers are automatically converted to strings.
        """

        job = _SingleJob(self, self.securitytoken, self.job_name_prefix, self.max_tries, job_name, params, self.propagation, self.secret_params_re, self.allow_missing_jobs)
        self.jobs.append(job)
        return job

    def invoke_unchecked(self, job_name, **params):
        """Define a Jenkins job that will be invoked under control of the surrounding flow, but will never cause the flow to fail.

        The job is always run in parallel with other jobs in the flow, even when invoked in a serial flow.
        It is not started out of order, but following jobs will be started immediately after this is started.
        The job will be monitored and reported on, only as long as regular "checked" jobs are still running.
        If it fails, it may be retried (depending on surrounding flows max_tries option), but only as long as regular jobs are still running.
        If the job is still running when all normal jobs are finished, the flow will exit, and the job is left running.

        See :py:meth:`invoke` for parameter description.
        """

        job = _SingleJob(self, self.securitytoken, self.job_name_prefix, self.max_tries, job_name, params, Propagation.UNCHECKED, self.secret_params_re, self.allow_missing_jobs)
        self.jobs.append(job)
        return job

    def _prepare_first(self):
        print(self.indentation + self._enter_str)
        self._prepare_to_invoke()
        for job in self.jobs:
            job._prepare_first()
        print(self.indentation + self._exit_str)

    def _show_job_definition(self):
        for job in self.jobs:
            job._show_job_definition()

    def _final_status(self):
        print(self.indentation + self._enter_str)
        for job in self.jobs:
            job._final_status()
        print(self.indentation + self._exit_str)

    def _check_timeout(self):
        now = hyperspeed.time()
        if self.timeout and now - self.invocation_time > self.timeout:
            unfinished_msg = ". Unfinished jobs:" + repr([job.sequence() for job in self.jobs if job.checking_status == Checking.MUST_CHECK])
            raise FlowTimeoutException("Timeout " + self._time_msg() + ", in flow " + str(self) + unfinished_msg, self.propagation)

    def __enter__(self):
        print(self.indentation + self._enter_str)
        super(_Flow, self).__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type:
            return None

        print(self.indentation + self._exit_str)
        super(_Flow, self).__exit__(exc_type, exc_value, traceback)
        if self.parent_flow:
            # Insert myself in parent if I'm not empty
            if self.jobs:
                self.parent_flow.jobs.append(self)
                return

            print(self.indentation + "INFO: Ignoring empty flow")
        print()

    def _check_invoke_report(self):
        if self._must_invoke_set_invocation_time():
            self._invocation_message('Flow', self)

        now = hyperspeed.time()
        report_now = now - self.last_report_time >= self.report_interval
        if report_now:
            self.last_report_time = now
        return report_now

    def report_result(self):
        # Pylint does not like Enum pylint: disable=no-member
        unchecked = (Propagation.UNCHECKED.name + ' ') if self.propagation == Propagation.UNCHECKED else ''
        print('Flow ' + unchecked + self.result.name, self, self._time_msg())

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
    _enter_str = "parallel flow: ("
    _exit_str = ")\n"

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

            if self.result in _build_result_failures:
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
    _enter_str = "serial flow: ["
    _exit_str = "]\n"

    def __init__(self, parent_flow, securitytoken, timeout, job_name_prefix='', max_tries=1, propagation=Propagation.NORMAL,
                 report_interval=None, secret_params=_default_secret_params_re, allow_missing_jobs=None):
        super(_Serial, self).__init__(parent_flow, securitytoken, timeout, job_name_prefix, max_tries, propagation,
                                      report_interval, secret_params, allow_missing_jobs)
        self.job_index = 0

    def _prepare_to_invoke(self, reset_tried_times=False):
        super(_Serial, self)._prepare_to_invoke(reset_tried_times)
        self.job_index = 0

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

            if self.result in _build_result_failures:
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
                      json_dir, json_indent, json_strip_top_level_prefix, params_display_order):
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

        self.params_display_order = params_display_order

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
        if self.json_file:
            self.json(self.json_file, self.json_indent)

        if self.just_dump:
            return

        if not self.jobs:
            print("WARNING: Empty toplevel flow", self, "nothing to do.")
            return

        # Wait for jobs to finish
        print()
        print("--- Getting initial job status ---")
        self.api.poll()
        self._prepare_first()

        self._show_job_definition()

        if self.json_file:
            self.json(self.json_file, self.json_indent)

        # pylint: disable=attribute-defined-outside-init
        self.start_time = hyperspeed.time()
        self.last_report_time = self.start_time

        print()
        print("--- Starting flow ---")
        sleep_time = min(self.poll_interval, self.report_interval)
        try:
            while self.checking_status == Checking.MUST_CHECK:
                self.api.quick_poll()
                self._check(None)
                hyperspeed.sleep(sleep_time)
        finally:
            print()
            print("--- Final status ---")
            self._final_status()

        if self.result == BuildResult.UNSTABLE:
            set_build_result(self.username, self.password, 'unstable', direct_url=self.top_flow.direct_url)


class parallel(_Parallel, _TopLevelControllerMixin):
    """Defines a parallel flow where nested jobs or flows are executed simultaneously.

    See :py:class:`serial` and :py:meth:`_Flow.parallel` for a description.
    """

    def __init__(self, jenkins_api, timeout, securitytoken=None, username=None, password=None, job_name_prefix='', max_tries=1, propagation=Propagation.NORMAL,
                 report_interval=_default_report_interval, poll_interval=_default_poll_interval, secret_params=_default_secret_params_re, allow_missing_jobs=False,
                 json_dir=None, json_indent=None, json_strip_top_level_prefix=True, direct_url=None, require_idle=True, just_dump=False, params_display_order=()):
        assert isinstance(propagation, Propagation)
        securitytoken = self.toplevel_init(jenkins_api, securitytoken, username, password, job_name_prefix, poll_interval, direct_url, require_idle,
                                           json_dir, json_indent, json_strip_top_level_prefix, params_display_order)
        super(parallel, self).__init__(self, timeout, securitytoken, job_name_prefix, max_tries, propagation, report_interval, secret_params, allow_missing_jobs)
        self.parent_flow = None
        self.just_dump = just_dump

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type:
            return None

        super(parallel, self).__exit__(exc_type, exc_value, traceback)
        self.wait_for_jobs()


class serial(_Serial, _TopLevelControllerMixin):
    """Defines a serial flow where nested jobs or flows are executed in order.

    Only differences to  :py:meth:`_Flow.serial` are described.

    Args:
        jenkins_api (:py:class:`.specialized_api.Jenkins` or :py:class:`.jenkinsapi_wrapper.Jenkins`): Jenkins Api instance used for accessing jenkins.
        securitytoken (str): Token to use on security enabled Jenkins instead of username/password. The Jenkins job must have the token configured.
        username (str): Name of user authorized to run Jenkins 'cli' and change job status.
        password (str): Password of user.
            The username/password here is are not used for running the jobs. See specialized_api for that.
        job_name_prefix (str): All jobs defined in flow will automatically be prefixed with this string before invoking Jenkins job.
        poll_interval (float): The interval in seconds between polling the status of unfinished Jenkins jobs.
        allow_missing_jobs (boolean): If true it is not considered an error if Jenkins jobs are missing when the flow starts.
            It is assumed that the missing jobs are created by other jobs in the flow
        json_dir (str): Directory in which to generate flow graph json file. If None, no flow graph is generated.
        json_indent (int): If not None json graph file is pretty printed with this indentation level.
        json_strip_top_level_prefix (boolean): If True, the job_name_prefix will be stripped from job names when generating json graph file
        direct_url (str): Non proxied url for accessing Jenkins
            Propagation.WARNING requires this as it uses the Jenkins cli, which will not work through a proxy, to set the build result
        require_idle (boolean): If True it is considered an error if any of the jobs in the flow are running when the flow starts
        just_dump (boolean): If True, the flow is just printed, no jobs are invoked.
        params_display_order (list): List of job parameter names used for ordering the parameters in the output.
            The format is [first1, ..., firstN, '*', last1, ..., lastN], where first..., last... are names that will be matched against the
            invoke **param names.
            Any of first..., '*', last... may be omitted
            Any parameters that are not matched will be displayes at the place of the '*', if specified, otherwise they will be displayed last.

    Returns:
        serial flow object

    Raises:
        JobControlException
    """

    def __init__(self, jenkins_api, timeout, securitytoken=None, username=None, password=None, job_name_prefix='', max_tries=1, propagation=Propagation.NORMAL,
                 report_interval=_default_report_interval, poll_interval=_default_poll_interval, secret_params=_default_secret_params_re, allow_missing_jobs=False,
                 json_dir=None, json_indent=None, json_strip_top_level_prefix=True, direct_url=None, require_idle=True, just_dump=False, params_display_order=()):
        assert isinstance(propagation, Propagation)
        securitytoken = self.toplevel_init(jenkins_api, securitytoken, username, password, job_name_prefix, poll_interval, direct_url, require_idle,
                                           json_dir, json_indent, json_strip_top_level_prefix, params_display_order)
        super(serial, self).__init__(self, timeout, securitytoken, job_name_prefix, max_tries, propagation, report_interval, secret_params, allow_missing_jobs)
        self.parent_flow = None
        self.just_dump = just_dump

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type:
            return None

        super(serial, self).__exit__(exc_type, exc_value, traceback)
        self.wait_for_jobs()
