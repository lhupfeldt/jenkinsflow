# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import os, re, abc, signal
from os.path import join as jp
from collections import OrderedDict
from itertools import chain
from enum import Enum

from .ordered_enum import OrderedEnum
from .jenkins_api import BuildResult, Progress, UnknownJobException


_default_poll_interval = 0.5
_default_report_interval = 5
_default_secret_params = '.*passw.*|.*PASSW.*'
_default_secret_params_re = re.compile(_default_secret_params)

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


class KillType(Enum):
    NONE = 0
    CURRENT = 1
    ALL = 2

    def __bool__(self):
        return self !=  KillType.NONE

    # Python2 compatibility
    __nonzero__ = __bool__


class JobControlException(Exception):
    def __init__(self, message, propagation=Propagation.NORMAL):
        super().__init__(message)
        self.propagation = propagation


class FlowTimeoutException(JobControlException):
    pass


class FlowScopeException(JobControlException):
    pass


class JobNotIdleException(JobControlException):
    pass


class MessageRedefinedException(JobControlException):
    pass


class JobControlFailException(JobControlException, metaclass=abc.ABCMeta):
    pass


class FailedSingleJobException(JobControlFailException):
    def __init__(self, job, propagation):
        msg = "Failed job: " + repr(job) + ", propagation:" + str(propagation)
        super().__init__(msg, propagation)


class MissingJobsException(JobControlFailException):
    def __init__(self, ex):
        super().__init__(str(ex), propagation=Propagation.NORMAL)


class FailedChildJobException(JobControlFailException):
    def __init__(self, flow_job, failed_child_job, propagation):
        msg = "Failed child job in: " + repr(flow_job) + ", child job:" + repr(failed_child_job) + ", propagation:" + str(propagation)
        super().__init__(msg, propagation)


class FailedChildJobsException(JobControlFailException):
    def __init__(self, flow_job, failed_child_jobs, propagation):
        msg = "Failed child jobs in: " + repr(flow_job) + ", child jobs:" + repr(failed_child_jobs) + ", propagation:" + str(propagation)
        super().__init__(msg, propagation)


class FinalResultException(JobControlFailException):
    def __init__(self, build_result):
        msg = "Flow Unsuccessful: {}".format(build_result)
        super().__init__(msg)
        self.result = build_result


class Killed(Exception):
    pass


class _JobControl(metaclass=abc.ABCMeta):
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
    def _invocation_id(self):
        """Must return an identification of invocation to distinguish multiple explicit invocations of the same job."""

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
        print("\n%s %s (%d/%d,%d/%d): %s" % (
            controller_type_name, self._invocation_id(), self.tried_times, self.max_tries, self.total_tried_times, self.total_max_tries, invocation_repr))

    def _must_invoke_set_invocation_time(self):
        if self.invocation_time:
            return False

        self.invocation_time = self.api.time()
        return True

    @abc.abstractmethod
    def _check(self, report_now):
        """Polled by flow controller until the job reaches state 'successful' or tried_times == parent.max_tries * self.max_tries"""

    def _time_msg(self):
        now = self.api.time()
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
        if self.result in (BuildResult.SUCCESS, BuildResult.SUPERSEDED) or self.propagation == Propagation.UNCHECKED:
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
        return max(self.max_tries - self.tried_times, 0)

    @property
    def remaining_total_tries(self):
        return max(self.total_max_tries - self.total_tried_times, 0)

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


class _SingleJobInvocation(_JobControl):
    """Represents a single flow-invocation of a Jenkins job.

    Multiple invocations of the same job in a single flow are allowed
    Retries are handled by the same instance of this class, but distinct invocations are handled by different instances.
    """

    def __init__(self, parent_flow, securitytoken, job_name_prefix, max_tries, job_name, params, propagation, secret_params_re, allow_missing_jobs):
        for key, value in params.items():
            # Handle parameters passed as int or bool. Booleans will be lowercased!
            if isinstance(value, (bool, int)):
                params[key] = str(value).lower()
        self.params = params
        super().__init__(parent_flow, securitytoken, max_tries, propagation, secret_params_re, allow_missing_jobs)
        # There is no separate retry for individual jobs, so set self.total_max_tries to the same as parent flow!
        self.total_max_tries = self.parent_flow.total_max_tries
        self.job = None
        self.job_invocation = None
        self.old_build_num = None
        self.name = job_name_prefix + job_name
        self.invocation_number = 0
        self.repr_str = ("unchecked " if self.propagation == Propagation.UNCHECKED else "") + "job: " + repr(self.name)
        self.jenkins_baseurl = None
        self._reported_invoked = False
        self._killed = False
        self._display_params = []
        self._set_display_params()

        print(self.indentation + repr(self))

    def _invocation_id(self):
        return ('Invocation-' + str(self.invocation_number)) if self.invocation_number != 0 else 'Invocation'

    def _prepare_first(self, require_job=False):
        previously_invoked = self.top_flow.jobs.get(self.name)
        if previously_invoked:
            if previously_invoked.invocation_number == 0:
                previously_invoked.invocation_number = 1
            self.invocation_number = previously_invoked.invocation_number + 1
        self.top_flow.jobs[self.name] = self

        try:
            self.job = self.api.get_job(self.name)
        except UnknownJobException as ex:
            # TODO? stack trace
            if require_job or not self.allow_missing_jobs and not self.top_flow.kill:
                self.checking_status = Checking.FINISHED
                self.result = BuildResult.FAILURE
                raise MissingJobsException(ex)
            print(self.indentation + repr(self), "- MISSING JOB")
            super()._prepare_to_invoke(reset_tried_times=False)
            return

        self._prepare_to_invoke()
        _result, progress, _ = self.job.job_status()
        if self.top_flow.require_idle and progress != Progress.IDLE and not self.top_flow.kill:
            # Pylint does not like Enum pylint: disable=no-member
            raise JobNotIdleException(repr(self) + " is in state " + progress.name + ". It must be " + Progress.IDLE.name + '.')

        if not previously_invoked:
            # TODO: Don't poll more than once per job for initial status
            print(self.indentation + self._status_message(progress, self.old_build_num, None, 'latest '))

    def _set_display_params(self):
        first = current = OrderedDict()
        last = OrderedDict()

        display_params = dict((key, (value if not self.secret_params_re.search(key) else '******')) for key, value in self.params.items())
        for name in self.top_flow.params_display_order:
            if name == '*':
                current = last
            if name in display_params:
                current[name] = display_params[name]
                del display_params[name]

        for key, value in chain(first.items(), sorted(display_params.items()), last.items()):
            self._display_params.append((key, repr(value)))

    def _show_job_definition(self):
        if self.job:
            print('Defined', self._invocation_id(), self.job.public_uri + (' - parameters:' if self._display_params else ''))
        else:
            print('Defined', self._invocation_id(), repr(self.name) + " - MISSING JOB")
        for key, value in self._display_params:
            print("    ", key, '=', value)
        if self._display_params:
            print("")

    def __repr__(self):
        if self.invocation_number == 0:
            return self.repr_str
        return self.repr_str + ' ' + self._invocation_id()

    def _invoked_message(self):
        print("Build started:", repr(self.name), self._invocation_id() + ' -' if self.invocation_number else '-', self.job_invocation.console_url())

    def _status_message(self, progress, build_num, queued_why, latest=''):
        if progress == Progress.QUEUED:
            msg = (queued_why) if queued_why else ''
        else:
            msg = latest + "build: " + ('#' + str(build_num) if build_num else str(None))
        return repr(self) + " Status " + progress.name + " - " + msg

    def _prepare_to_invoke(self, reset_tried_times=False):
        super()._prepare_to_invoke(reset_tried_times)
        _, _, self.old_build_num = self.job.job_status()
        self._reported_invoked = False

    def _check(self, report_now):
        if self.job is None:
            self._prepare_first(require_job=True)

        self.job.poll()
        if self._must_invoke_set_invocation_time():
            # Don't re-invoke unchecked jobs that are still running
            if self.propagation != Propagation.UNCHECKED:
                self._invocation_message('Job', self.job.public_uri)
                params = self.params if self.params else None
                self.job_invocation = self.job.invoke(securitytoken=self.securitytoken, build_params=params,
                                                      cause=self.top_flow.cause, description=self.top_flow.description)
            elif not self.job_invocation or self.job_invocation.status()[1] == Progress.IDLE:
                self._invocation_message('Job', self.job.public_uri)
                params = self.params if self.params else None
                self.job_invocation = self.job.invoke(securitytoken=self.securitytoken, build_params=params, cause=self.top_flow.cause,
                                                      description=self.top_flow.description)

        result, progress = self.job_invocation.status()
        if not self._reported_invoked and self.job_invocation.build_number is not None:
            if result != BuildResult.SUPERSEDED:
                self._invoked_message()
            self._reported_invoked = True

        if result == BuildResult.UNKNOWN:
            if report_now:
                build_num = self.job_invocation.build_number if self.job_invocation.build_number else self.old_build_num
                print(self._status_message(progress, build_num, self.job_invocation.queued_why))
            return

        # The job has stopped running
        self.checking_status = Checking.FINISHED
        self.result = result

        # Pylint does not like Enum pylint: disable=no-member
        unchecked = (Propagation.UNCHECKED.name + ' ') if self.propagation == Propagation.UNCHECKED else ''

        inv_id_msg = (' ' + self._invocation_id()) if self.invocation_number else ''
        if result != BuildResult.SUPERSEDED:
            print(self, "stopped running")
            print(self._status_message(progress, self.job_invocation.build_number, self.job_invocation.queued_why))
            # Pylint does not like Enum pylint: disable=maybe-no-member
            print(unchecked + self.result.name + ":", repr(self.job.name) + inv_id_msg, "- build:", self.job_invocation.console_url(), self._time_msg())

            if self.result in _build_result_failures:
                raise FailedSingleJobException(self.job, self.propagation)
            return

        # Pylint does not like Enum pylint: disable=maybe-no-member
        print(unchecked + self.result.name + ":", repr(self.job.name) + inv_id_msg)

    def _kill_check(self, report_now, dequeue):
        if self.job is None:
            print(self, "no job")
            self.checking_status = Checking.FINISHED
            return

        self.job.poll()
        if not self._killed:
            self._killed = not dequeue
            if self.top_flow.kill == KillType.ALL:
                if not dequeue:
                    print("Killing all running builds for:", repr(self.name))
                self.job.stop_all()
            elif self.job_invocation:
                if not dequeue:
                    print("Killing build:", repr(self.name), '-', self.job_invocation.console_url())
                self.job_invocation.stop(dequeue)
            else:
                print("Not invoked:", repr(self.name))

        if self.top_flow.kill == KillType.ALL:
            self.result, progress, current_build_num = self.job.job_status()
            if progress != Progress.IDLE and self.old_build_num == current_build_num:
                if report_now and not dequeue:
                    print(self._status_message(progress, None, self.job.queued_why))
                return
        elif self.job_invocation:
            self.result, progress = self.job_invocation.status()
            if progress != Progress.IDLE:
                if report_now and not dequeue:
                    print(self._status_message(progress, self.job_invocation.build_number, self.job_invocation.queued_why))
                return

        # The job has stopped running
        self.checking_status = Checking.FINISHED
        if self.top_flow.kill == KillType.ALL:
            if self.old_build_num == current_build_num:
                print(self, "stopped running")
            else:
                print(self, "was invoked again after kill")
            print(self._status_message(progress, current_build_num, self.job.queued_why))
        elif self.job_invocation:
            print(self, "stopped running")
            print(self._status_message(progress, self.job_invocation.build_number, self.job_invocation.queued_why))

        # Pylint does not like Enum pylint: disable=maybe-no-member
        print(self.result.name + ":", repr(self.job.name))

    def sequence(self):
        return self.name

    def _final_status(self):
        if self.job is not None:
            # Pylint does not like Enum pylint: disable=maybe-no-member
            if self.result in (BuildResult.SUCCESS, BuildResult.SUPERSEDED) and not self.top_flow.kill:
                print(self.indentation + repr(self), self.result.name)
                return

            self.job.poll()
            if self.job_invocation:
                result, progress = self.job_invocation.status()
            else:
                if self.top_flow.kill == KillType.ALL:
                    result, progress, _ = self.job.job_status()
                else:
                    result, progress = BuildResult.UNKNOWN, Progress.IDLE
            progress_msg = ""
            if progress != Progress.IDLE or result == BuildResult.UNKNOWN or self.top_flow.kill:
                progress_msg = "- " + progress.name
            console_url = ""
            if self.result not in (BuildResult.UNKNOWN, BuildResult.DEQUEUED) and not (self.top_flow.kill == KillType.ALL) and self.job_invocation:
                console_url = self.job_invocation.console_url()
            assert isinstance(result, BuildResult)
            print(self.indentation + repr(self), result.name, progress_msg, console_url)
            return

        print(self.indentation + repr(self), "- MISSING JOB")

    def last_jobs_in_flow(self):
        return [self] if self.propagation != Propagation.UNCHECKED else []

    def nodes(self, node_to_id):
        node_name = self.name[self.top_flow.json_strip_index:]
        url = self.job.public_uri if self.job is not None else None

        # For performance reasons use abbreviations
        return [
            OrderedDict(
                (
                    ("id", node_to_id(self)),
                    ("name", node_name),
                    ("url", url),
                    ("tr", [self.max_tries, self.tried_times, self.total_max_tries, self.total_tried_times]),
                    ("nl", self.nesting_level),
                    ("pr", self.propagation.name),
                    # Pylint does not like Enum pylint: disable=maybe-no-member
                    ("cs", self.checking_status.name),
                    ("res", self.result.name),
                    ("it", self.invocation_time),
                    ("params", self._display_params),
                )
            )
        ]

    def links(self, prev_jobs, node_to_id):
        return [OrderedDict((("source", node_to_id(job)), ("target", node_to_id(self)))) for job in prev_jobs]


# Retries are handled in the _Flow classes instead of _SingleJobInvocation since the individual jobs don't know
# how to retry. The _Serial flow is retried from start of flow and in _Parallel flow individual jobs
# are retried immediately

class _Flow(_JobControl, metaclass=abc.ABCMeta):
    _enter_str = None
    _exit_str = None

    def __init__(self, parent_flow, timeout, securitytoken, job_name_prefix, max_tries, propagation, report_interval, secret_params, allow_missing_jobs):
        secret_params_re = re.compile(secret_params) if isinstance(secret_params, str) else secret_params
        super().__init__(parent_flow, securitytoken, max_tries, propagation, secret_params_re, allow_missing_jobs)
        self.timeout = timeout
        self.job_name_prefix = self.parent_flow.job_name_prefix + job_name_prefix if job_name_prefix is not None else ""
        self.report_interval = report_interval or self.parent_flow.report_interval

        self.invocations = []
        self.last_report_time = 0
        self.last_json_time = 0
        self._failed_child_jobs = {}
        self._can_raise_kill = False

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
            timeout (float): Maximum time in seconds to wait for flow jobs to finish. 0 means infinite, however, this flow can not run longer than
                the minimum timeout of any parent flows. Note that jenkins jobs are NOT terminated when the flow times out.

            securitytoken (str): Token to use on security enabled Jenkins instead of username/password. The Jenkins job must have the token configured.
                If None, the parent flow securitytoken is used.

            job_name_prefix (str): All jobs defined in flow will automatically be prefixed with the parent flow job_name_prefix + this job_name_prefix
                before invoking Jenkins job. To reset prefixing (i.e. don't use parent flow prefix either), set the value to None

            max_tries (int): Maximum number of times to invoke the flow. Default is 1, meaning no retry will be attempted in case a job fails.
                If a job fails, jobs are retried from start of the parallel flow::

                    with serial(..., max_tries=3) as sf:
                        sf.invoke('a', ...)
                        sf.invoke('b', ...)  # fail -> restart flow from job 'a'
                        sf.invoke('c', ...)

                Retries may be nested::

                    with parallel(..., max_tries=2) as pf:
                        with pf.serial(..., max_tries=3) as sf:
                            sf.invoke('a', ...)  # If job 'a' fails it could be invoked up to 6 times

            propagation (Propagation): How to propagate errors from failed Jenkins jobs.
                This can be used to downgrade a 'FAILURE' result to 'UNSTABLE'.
                This will not change the result of a failed job, the result of jobs are used in caculating the propagated result. E.g::

                    with parallel(...) as pf:
                        with pf.serial(..., propagation=Propagation.UNSTABLE) as sf1:
                            sf1.invoke('a', ...)  # If job 'a' fails the result propagated to sf1 will be 'UNSTABLE' and sf1 will propagate
                                                  #  'UNSTABLE' on to pf

                        with pf.serial(...) as sf2:
                            sf2.invoke('b', ...)  # If job 'b' fails the result propagated to sf2 and pf will be 'FAILURE'

                    sys.exit(77 if pf.result == Propagation.UNSTABLE else 0)
                    # Assuming the Jenkins job was configured with 'Exit code to set build unstable==77'

                NOTE: You must make sure that the jobs are configured correctly and that the correct exit code is used in the shell step, otherwise
                the propagation value will have no effect on the final job status.
                NOTE: Also see the raise_if_unsuccessful argument to the top level `serial` and `parallel` flows.

            report_interval (float): The interval in seconds between reporting the status of polled Jenkins jobs.
                If None the parent flow report_interval is used.

            secret_params (re.RegexObject): Regex of Jenkins job invocation parameter names, for which the value will be masked out with '******' when
                parameters are printed.
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
        """Define a Jenkins job invocation that will be invoked under control of the surrounding flow.

        This does not create the job in Jenkins. It defines how the job will be invoked by ``jenkinsflow``.

        Args:
            job_name (str): The last part of the name of the job in jenkins.
                If the surrounding flow sets the :py:obj:`job_name_prefix` the actual name of the invoked job will be the parent flow job_name_prefix + job_name.
            **params (str, int, boolean): Arguments passed to Jenkins when invoking the job. Strings are passed as they are,
                booleans are automatically converted to strings and lowercased, integers are automatically converted to strings.
        """

        inv = _SingleJobInvocation(self, self.securitytoken, self.job_name_prefix, self.max_tries, job_name, params, self.propagation, self.secret_params_re, self.allow_missing_jobs)
        self.invocations.append(inv)
        return inv

    def invoke_unchecked(self, job_name, **params):
        """Define a Jenkins job invocation that will be invoked under control of the surrounding flow, but will never cause the flow to fail.

        The job is always run in parallel with other jobs in the flow, even when invoked in a serial flow.
        It is not started out of order, but following jobs will be started immediately after this is started.
        The job will be monitored and reported on, only as long as regular "checked" jobs are still running.
        If it fails, it may be retried (depending on surrounding flows max_tries option), but only as long as regular jobs are still running.
        If the job is still running when all normal jobs are finished, the flow will exit, and the job is left running.

        See :py:meth:`invoke` for parameter description.
        """

        inv = _SingleJobInvocation(self, self.securitytoken, self.job_name_prefix, self.max_tries, job_name, params, Propagation.UNCHECKED, self.secret_params_re, self.allow_missing_jobs)
        self.invocations.append(inv)
        return inv

    def _invocation_id(self):
        return 'Invocation'

    def _prepare_first(self):
        print(self.indentation + self._enter_str)
        self._prepare_to_invoke()
        for inv in self.invocations:
            inv._prepare_first()
        print(self.indentation + self._exit_str)

    def _show_job_definition(self):
        for inv in self.invocations:
            inv._show_job_definition()

    def _final_status(self):
        print(self.indentation + self._enter_str)
        for inv in self.invocations:
            inv._final_status()
        print(self.indentation + self._exit_str)

    def _check_timeout(self):
        now = self.api.time()
        if self.timeout and now - self.invocation_time > self.timeout:
            unfinished_msg = ". Unfinished jobs:" + repr([inv.sequence() for inv in self.invocations if inv.checking_status == Checking.MUST_CHECK])
            raise FlowTimeoutException("Timeout " + self._time_msg() + ", in flow " + str(self) + unfinished_msg, self.propagation)

    def __enter__(self):
        print(self.indentation + self._enter_str)
        super().__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type:
            return None

        print(self.indentation + self._exit_str)
        super().__exit__(exc_type, exc_value, traceback)
        if self.parent_flow:
            # Insert myself in parent if I'm not empty
            if self.invocations:
                self.parent_flow.invocations.append(self)
                return

            print(self.indentation + "INFO: Ignoring empty flow")
        print()

    def _check_report(self):
        now = self.api.time()
        report_now = now - self.last_report_time >= self.report_interval
        if report_now:
            self.last_report_time = now
        return report_now

    def _check_invoke_report(self):
        if self._must_invoke_set_invocation_time():
            self._invocation_message('Flow', self)
        return self._check_report()

    def _kill_check(self, report_now, dequeue):
        report_now = self._check_report()

        checking_status = Checking.FINISHED
        for inv in self.invocations:
            if inv.checking_status != Checking.FINISHED:
                inv._kill_check(report_now, dequeue)
                job_propagate_checking_status = inv.checking_status if inv.checking_status != Checking.HAS_UNCHECKED else Checking.MUST_CHECK
                checking_status = min(checking_status, job_propagate_checking_status)

        self.checking_status = checking_status
        if self.checking_status == Checking.FINISHED:
            # All jobs have stopped running
            for inv in self.invocations:
                self.result = min(self.result, inv.propagate_result)
            self.report_result()

    def report_result(self):
        # Pylint does not like Enum pylint: disable=no-member
        unchecked = (Propagation.UNCHECKED.name + ' ') if self.propagation == Propagation.UNCHECKED else ''
        # Pylint does not like Enum pylint: disable=maybe-no-member
        print('Flow ' + unchecked + self.result.name, self, self._time_msg())

    def json(self, file_path, indent=None):
        node_to_id = lambda job: job.node_id
        separators=None
        if indent:
            node_to_id = lambda job: job.name
            separators=(',', ': ')

        nodes = self.nodes(node_to_id)
        links = self.links([], node_to_id)
        graph = OrderedDict((('nodes', nodes), ('links', links)))

        import json
        from atomicfile import AtomicFile
        if file_path is not None:
            with AtomicFile(file_path, 'w+') as out_file:
                # python3 doesn't need  separators=(',', ': ')
                json.dump(graph, out_file, indent=indent, separators=separators)
        else:
            # python3 doesn't need  separators=(',', ': ')
            return json.dumps(graph, indent=indent, separators=separators)


class _Parallel(_Flow):
    _enter_str = "parallel flow: ("
    _exit_str = ")\n"

    def _check(self, report_now):
        report_now = self._check_invoke_report()

        checking_status = Checking.FINISHED
        for inv in self.invocations:
            try:
                if inv.checking_status != Checking.FINISHED:
                    inv._check(report_now)
                    checking_status = min(checking_status, inv.propagate_checking_status)
                    if id(inv) in self._failed_child_jobs:
                        del self._failed_child_jobs[id(inv)]
            except JobControlFailException:
                self._failed_child_jobs[id(inv)] = inv

                if inv.result == BuildResult.ABORTED:
                    if inv.remaining_tries or inv.remaining_total_tries:
                        print("ABORTED:", inv, "not retrying")
                    inv.checking_status = Checking.FINISHED
                    continue

                if inv.remaining_tries:
                    print("RETRY:", inv, "failed but will be retried. Up to", inv.remaining_tries, "more times in current flow")
                    checking_status = Checking.MUST_CHECK
                    inv._prepare_to_invoke()
                    continue

                if inv.remaining_total_tries:
                    print("RETRY:", inv, "failed but will be retried. Up to", inv.remaining_total_tries, "more times through outer flow")
                    inv._prepare_to_invoke(reset_tried_times=True)
                    continue

                inv.checking_status = Checking.FINISHED

        self.checking_status = checking_status
        if self.checking_status != Checking.MUST_CHECK and self.result == BuildResult.UNKNOWN:
            # All jobs have stopped running or are 'unchecked'
            for inv in self.invocations:
                self.result = min(self.result, inv.propagate_result)
            self.report_result()

            if self.result in _build_result_failures:
                raise FailedChildJobsException(self, self._failed_child_jobs.values(), self.propagation)
        else:
            self._check_timeout()

    def sequence(self):
        return tuple([inv.sequence() for inv in self.invocations])

    def last_jobs_in_flow(self):
        invocations = []
        for inv in self.invocations:
            invocations.extend(inv.last_jobs_in_flow())
        return invocations

    def nodes(self, node_to_id):
        nodes = []
        for inv in self.invocations:
            child_nodes = inv.nodes(node_to_id)
            nodes.extend(child_nodes)
        return nodes

    def links(self, prev_jobs, node_to_id):
        links = []
        for inv in self.invocations:
            child_links = inv.links(prev_jobs, node_to_id)
            links.extend(child_links)
        return links


class _Serial(_Flow):
    _enter_str = "serial flow: ["
    _exit_str = "]\n"

    def __init__(self, parent_flow, securitytoken, timeout, job_name_prefix='', max_tries=1, propagation=Propagation.NORMAL,
                 report_interval=None, secret_params=_default_secret_params_re, allow_missing_jobs=None):
        super().__init__(parent_flow, securitytoken, timeout, job_name_prefix, max_tries, propagation,
                                      report_interval, secret_params, allow_missing_jobs)
        self.job_index = 0

    def _prepare_to_invoke(self, reset_tried_times=False):
        super()._prepare_to_invoke(reset_tried_times)
        self.job_index = 0

    def _check(self, report_now):
        report_now = self._check_invoke_report()

        checking_status = Checking.FINISHED
        for inv in self.invocations[0:self.job_index + 1]:
            try:
                if inv.checking_status != Checking.FINISHED:
                    inv._check(report_now)
                    checking_status = min(checking_status, inv.propagate_checking_status)
            except JobControlFailException:
                if inv.result == BuildResult.ABORTED:
                    if inv.remaining_tries or inv.remaining_total_tries:
                        print("ABORTED:", inv, "not retrying")
                    inv.checking_status = Checking.FINISHED
                    self.total_max_tries = 0
                    self.max_tries = 0
                    continue

                # The job has stopped running
                if inv.remaining_tries:
                    if inv.propagation != Propagation.NORMAL:
                        print("MAY RETRY:", inv, inv.propagation, " failed, will only retry if checked failures. Up to", inv.remaining_tries, "more times in current flow")
                        continue
                    print("RETRY:", inv, "failed, retrying child jobs from beginning. Up to", inv.remaining_tries, "more times in current flow")
                    checking_status = Checking.MUST_CHECK
                    for pre_job in self.invocations[0:self.job_index + 1]:
                        pre_job._prepare_to_invoke()
                    self.job_index = 0
                    continue

                if inv.remaining_total_tries:
                    if inv.propagation != Propagation.NORMAL:
                        print("MAY RETRY:", inv, inv.propagation, " failed, will only retry if checked failures. Up to", inv.remaining_total_tries, "more times through outer flow")
                        continue
                    print("RETRY:", inv, "failed, retrying child jobs from beginning. Up to", inv.remaining_total_tries, "more times through outer flow")
                    for pre_job in self.invocations[0:self.job_index + 1]:
                        pre_job._prepare_to_invoke(reset_tried_times=True)
                    self.job_index = 0
                    continue

                inv.checking_status = Checking.FINISHED
                if inv.propagation != Propagation.UNCHECKED:
                    self.job_index = len(self.invocations)

        self.checking_status = checking_status
        if self.checking_status != Checking.MUST_CHECK and self.result == BuildResult.UNKNOWN:
            for inv in self.invocations[0:self.job_index + 1]:
                self.result = min(self.result, inv.propagate_result)

            if self.result in _build_result_failures:
                self.report_result()
                raise FailedChildJobException(self, inv, self.propagation)

            self.job_index += 1
            if self.job_index < len(self.invocations):
                self.checking_status = Checking.MUST_CHECK
                self.result = BuildResult.UNKNOWN
                return

            # All jobs have stopped running or are 'unchecked'
            self.report_result()
        else:
            self._check_timeout()

    def sequence(self):
        return [inv.sequence() for inv in self.invocations]

    def last_jobs_in_flow(self):
        for inv in self.invocations[-1:0:-1]:
            last_jobs = inv.last_jobs_in_flow()
            if last_jobs:
                return last_jobs
        return []

    def nodes(self, node_to_id):
        nodes = []
        for inv in self.invocations:
            child_nodes = inv.nodes(node_to_id)
            nodes.extend(child_nodes)
        return nodes

    def links(self, prev_jobs, node_to_id):
        links = []
        for inv in self.invocations:
            child_links = inv.links(prev_jobs, node_to_id)
            links.extend(child_links)
            prev_jobs = inv.last_jobs_in_flow()
        return links


class _TopLevelControllerMixin(metaclass=abc.ABCMeta):
    def toplevel_init(self, jenkins_api, securitytoken, username, password, top_level_job_name_prefix, poll_interval, direct_url, require_idle,
                      json_dir, json_indent, json_strip_top_level_prefix, params_display_order, just_dump, kill_all, description, raise_if_unsuccessful):
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
        self.just_dump = just_dump

        self.kill = KillType.ALL if kill_all else KillType.NONE

        jenkins_job_name = os.environ.get('JOB_NAME')
        if jenkins_job_name:
            self.cause = "By flow job " + repr(jenkins_job_name) + ' #' +  os.environ.get('BUILD_NUMBER', ' None')
        else:
            import getpass
            user = getpass.getuser()
            self.cause = "By flow script, user: " + user

        self._api = jenkins_api
        self.securitytoken = securitytoken
        self.username = username or self._api.username
        self.password = password or self._api.password
        self.poll_interval = poll_interval
        self.direct_url = direct_url.rstrip('/') if direct_url is not None else direct_url
        self.require_idle = require_idle

        self.json_dir = json_dir
        self.json_indent = json_indent
        self.json_strip_index = len(top_level_job_name_prefix) if json_strip_top_level_prefix else 0
        self.json_file = jp(self.json_dir, 'flow_graph.json') if json_dir is not None else None

        self.params_display_order = params_display_order
        self.description = description
        self.raise_if_unsuccessful = raise_if_unsuccessful

        # 'jobs' hold unique jobs by name vs 'invocations' on individual flows which may hold multiple invocations on one job
        self.jobs = {}

        # Set signalhandler to kill entire flow
        def set_kill(_sig, _frame):
            print("\nGot SIGTERM: Killing all builds belonging to current flow")
            self.kill = KillType.CURRENT
            if self._can_raise_kill:
                raise Killed()
        signal.signal(signal.SIGTERM, set_kill)

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
        print("Invocation-N (w/x,y/z): ")
        print("    -N: 'Invocation N of same job', where N is invocation number which is increased every time a job has been explicitly")
        print("            invoked (as opposed to retried). '-N' is only present for jobs with multiple invocations.")
        print("    w=current retry invocation in current flow scope, x=max in scope, y=total number of invocations, z=total max invocations")
        print("Elapsed time: 'after: x/y': x=time spent during current run of job, y=time elapsed since start of outermost flow")
        print()
        print("--- Calculating flow graph ---")

    def wait_for_jobs(self):
        if self.json_file:
            self.json(self.json_file, self.json_indent)

        if self.just_dump:
            return

        if not self.invocations:
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
        self.start_time = self._api.time()
        self.last_report_time = self.start_time
        last_json_time = self.start_time
        json_interval = max(30, self.report_interval)

        print()
        if not self.kill:
            print("--- Starting flow ---")
        else:
            print("--- Starting kill of all builds in flow ---")

        sleep_time = min(self.poll_interval, self.report_interval)
        try:
            dequeue = True
            while self.checking_status == Checking.MUST_CHECK:
                self.api.quick_poll()
                if not self.kill:
                    try:
                        self._can_raise_kill = True
                        self._check(None)
                        self._can_raise_kill = False
                    except Killed:
                        pass
                else:
                    self.api.queue_poll()
                    self._kill_check(None, dequeue)
                    dequeue = False

                self._api.sleep(sleep_time)
                if self.json_file:
                    now = self._api.time()
                    json_now = now - last_json_time >= json_interval
                    if json_now:
                        last_json_time = now
                    self.json(self.json_file, self.json_indent)

            if self.raise_if_unsuccessful and self.result != BuildResult.SUCCESS and self.kill != KillType.ALL:
                raise FinalResultException(self.result)
        finally:
            print()
            print("--- Final status ---")
            self.api.quick_poll()
            self._final_status()
            if self.json_file:
                self.json(self.json_file, self.json_indent)


class parallel(_Parallel, _TopLevelControllerMixin):
    """Defines a parallel flow where nested jobs or flows are executed simultaneously.

    See :py:class:`serial` and :py:meth:`_Flow.parallel` for a description.
    """

    def __init__(self, jenkins_api, timeout, securitytoken=None, username=None, password=None, job_name_prefix='', max_tries=1, propagation=Propagation.NORMAL,
                 report_interval=_default_report_interval, poll_interval=_default_poll_interval, secret_params=_default_secret_params_re, allow_missing_jobs=False,
                 json_dir=None, json_indent=None, json_strip_top_level_prefix=True, direct_url=None, require_idle=True, just_dump=False, params_display_order=(),
                 kill_all=False, description=None, raise_if_unsuccessful=True):
        assert isinstance(propagation, Propagation)
        securitytoken = self.toplevel_init(jenkins_api, securitytoken, username, password, job_name_prefix, poll_interval, direct_url, require_idle,
                                           json_dir, json_indent, json_strip_top_level_prefix, params_display_order, just_dump, kill_all, description=description,
                                           raise_if_unsuccessful=raise_if_unsuccessful)
        super().__init__(self, timeout, securitytoken, job_name_prefix, max_tries, propagation, report_interval, secret_params, allow_missing_jobs)
        self.parent_flow = None

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type:
            return None

        super().__exit__(exc_type, exc_value, traceback)
        self.wait_for_jobs()


class serial(_Serial, _TopLevelControllerMixin):
    r"""Defines a serial flow where nested jobs or flows are executed in order.

    Only differences to  :py:meth:`_Flow.serial` are described.

    Args:
        jenkins_api (:py:class:`.jenkins_api.Jenkins` or :py:class:`.script_api.Jenkins`): Jenkins Api instance used for accessing jenkins.
            If jenkins_api is instantiated with username/password you do not need to specify username/password to the flow (see below).

        securitytoken (str): Token to use on security enabled Jenkins instead of username/password. The Jenkins job must have the token configured.

        username (str): Name of user authorized to run Jenkins 'cli' and change job status.

        password (str): Password of user.
            The username/password here is are not used for running the jobs. See jenkins_api for that.
            If username/password is specified for jenkins_api, they will be used unless they are also specified on the flow.

        job_name_prefix (str): All jobs defined in flow will automatically be prefixed with this string before invoking Jenkins job.

        poll_interval (float): The interval in seconds between polling the status of unfinished Jenkins jobs.

        allow_missing_jobs (boolean): If true it is not considered an error if Jenkins jobs are missing when the flow starts.
            It is assumed that the missing jobs are created by other jobs in the flow

        json_dir (str): Directory in which to generate flow graph json file. If None, no flow graph is generated.

        json_indent (int): If not None json graph file is pretty printed with this indentation level.

        json_strip_top_level_prefix (boolean): If True, the job_name_prefix will be stripped from job names when generating json graph file

        direct_url (str): Non proxied url for accessing Jenkins, use this as an optimization to avoid routing rest calls from Jenkins through
            a proxy if the JENKINS_URL setting does not point directly to jenkins.

        require_idle (boolean): If True it is considered an error if any of the jobs in the flow are running when the flow starts.

        just_dump (boolean): If True, the flow is just printed, no jobs are invoked.

        params_display_order (list): List of job parameter names used for ordering the parameters in the output.
            The format is [first1, ..., firstN, '\*', last1, ..., lastN], where first..., last... are names that will be matched against the
            invoke \*\*param names.
            Any of first..., '*', last... may be omitted
            Any parameters that are not matched will be displayes at the place of the '*', if specified, otherwise they will be displayed last.

        kill_all (boolean): If True, all running builds for jobs defined in the flow will be aborted, regardless which flow invocation
            started the build.
            Note: It also possible to send SIGTERM to an already running flow to make the flow abort all builds started by the current
            invocation of the flow, but not builds started by other invocations of the same flow.

        raise_if_unsuccessful (bool): If the result of the outermost flow is not `BuildResult.SUCCESS` and no exception was raised, then
            a `FinalResultException` will be raised. The result property of this exception should be checked and the proper value returned
            from the shell step. Use in combination with the 'Exit code to set build unstable' feature in the advanced section on freestyle
            jobs shell build step. E.g::

                try:
                    with parallel(api) as ctrl1:
                        ctrl1.invoke('j11')

                        with ctrl1.serial() as ctrl2:
                            ctrl2.invoke('j21')  # ends succesfully
                            ctrl2.invoke('j22')  # ends in state UNSTABLE
                            ctrl2.invoke('j23')

                except FinalResultException as ex:
                    if ex.result == BuildResult.UNSTABLE:
                        return 77
                    raise

            If set to False, then the propagated reult value is available as the attribute 'result' on the top level flow, so that it can be used to
            return the proper value.

    Returns:
        serial flow object

    Raises:
        JobControlException
    """

    def __init__(self, jenkins_api, timeout, securitytoken=None, username=None, password=None, job_name_prefix='', max_tries=1, propagation=Propagation.NORMAL,
                 report_interval=_default_report_interval, poll_interval=_default_poll_interval, secret_params=_default_secret_params_re, allow_missing_jobs=False,
                 json_dir=None, json_indent=None, json_strip_top_level_prefix=True, direct_url=None, require_idle=True, just_dump=False, params_display_order=(),
                 kill_all=False, description=None, raise_if_unsuccessful=True):
        assert isinstance(propagation, Propagation)
        securitytoken = self.toplevel_init(jenkins_api, securitytoken, username, password, job_name_prefix, poll_interval, direct_url, require_idle,
                                           json_dir, json_indent, json_strip_top_level_prefix, params_display_order, just_dump, kill_all, description=description,
                                           raise_if_unsuccessful=raise_if_unsuccessful)
        super().__init__(self, timeout, securitytoken, job_name_prefix, max_tries, propagation, report_interval, secret_params, allow_missing_jobs)
        self.parent_flow = None

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type:
            return None

        super().__exit__(exc_type, exc_value, traceback)
        self.wait_for_jobs()
