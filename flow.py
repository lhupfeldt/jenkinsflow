# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

import os, time, re, abc
from set_build_result import set_build_result

_default_report_interval = 5
_default_secret_params = '.*passw.*|.*PASSW.*'
_default_secret_params_re = re.compile(_default_secret_params)

_debug = False

class JobControlException(Exception):
    def __init__(self, message, warn_only=False):
        super(JobControlException, self).__init__(message)
        self.warn_only = warn_only


class FlowTimeoutException(JobControlException):
    pass


class FlowScopeException(JobControlException):
    pass


class JobControlFailException(JobControlException):
    __metaclass__ = abc.ABCMeta


class FailedSingleJobException(JobControlFailException):
    def __init__(self, job, warn_only):
        msg = "Failed job: " + repr(job) + ", warn_only:" + str(warn_only)
        super(FailedSingleJobException, self).__init__(msg, warn_only)


class MissingJobsException(FailedSingleJobException):
    def __init__(self, job):
        msg = "Could not get job info: " + repr(job)
        super(MissingJobsException, self).__init__(msg, warn_only=False)


class FailedChildJobException(JobControlFailException):
    def __init__(self, flow_job, failed_child_job, warn_only):
        msg = "Failed child job in: " + repr(flow_job) + ", child job:" + repr(failed_child_job) + ", warn_only:" + str(warn_only)
        super(FailedChildJobException, self).__init__(msg, warn_only)


class FailedChildJobsException(JobControlFailException):
    def __init__(self, flow_job, failed_child_jobs, warn_only):
        msg = "Failed child jobs in: " + repr(flow_job) + ", child jobs:" + repr(failed_child_jobs) + ", warn_only:" + str(warn_only)
        super(FailedChildJobsException, self).__init__(msg, warn_only)


class _JobControl(object):
    __metaclass__ = abc.ABCMeta

    RESULT_FAIL = 0
    RESULT_UNSTABLE = 1
    RESULT_UNCHECKED = 2
    RESULT_SUCCESS = 3

    def __init__(self, parent_flow, securitytoken, max_tries, warn_only, report_interval, secret_params_re, allow_missing_jobs):
        self.parent_flow = parent_flow
        self.top_flow = parent_flow.top_flow

        self.max_tries = max_tries
        self.total_max_tries = self.max_tries * self.parent_flow.total_max_tries

        self.nesting_level = self.parent_flow.nesting_level + 1
        if self.nesting_level != self.top_flow.current_nesting_level + 1:
            raise FlowScopeException("Flow used out of scope")

        self.securitytoken = securitytoken or self.parent_flow.securitytoken
        self.warn_only = warn_only
        self.report_interval = report_interval or self.parent_flow.report_interval
        self.secret_params_re = secret_params_re or self.parent_flow.secret_params_re
        self.allow_missing_jobs = allow_missing_jobs if allow_missing_jobs is not None else self.parent_flow.allow_missing_jobs

        self.result = self.RESULT_FAIL
        self.tried_times = 0
        self.total_tried_times = 0
        self.invocation_time = None

    def __enter__(self):
        self.top_flow.current_nesting_level += 1

    def __exit__(self, exc_type, exc_value, traceback):
        self.top_flow.current_nesting_level -= 1

    def _prepare_first(self):
        self._prepare_to_invoke()

    def _jenkins_result_to_result(self, jenkinsresult):
        if jenkinsresult in ("PASSED", "SUCCESS"):
            return self.RESULT_SUCCESS
        if jenkinsresult in ("FAILED", "FAILURE", "FAIL"):
            return self.RESULT_FAIL
        if jenkinsresult == "UNSTABLE":
            return self.RESULT_UNSTABLE
        raise JobControlException("Unknown result type from build: " + str(jenkinsresult))

    def _prepare_to_invoke(self):
        """Must be called before each invocation of a job, as opposed to __init__, which is called once in entire run"""
        self.invocation_time = 0

    def _invoke_if_not_invoked(self):
        if self.invocation_time:
            return True

        self.invocation_time = time.time()
        print("\nInvoking (%d/%d,%d/%d):" % (self.tried_times + 1, self.max_tries, self.total_tried_times + 1, self.total_max_tries), self)
        return False

    @abc.abstractmethod
    def _check(self, start_time, last_report_time):
        """Polled by flow controller until the job reaches state 'successful' or tried_times == parent.max_tries * self.max_tries"""
        pass

    def _time_msg(self, start_time):
        now = time.time()
        return "after: %.3fs/%.3fs" % (now - self.invocation_time, now - start_time)

    @abc.abstractmethod
    def sequence(self):
        pass

    @property
    def indentation(self):
        return self.nesting_level * 3 * ' '

    @property
    def api(self):
        return self.top_flow._api

    def __repr__(self):
        return str(self.sequence())

    def debug(self, *args):
        if not _debug:
            return
        print('DEBUG in ' + self.__class__.__name__ + ':', ' '.join([str(arg) for arg in args]))


class _SingleJob(_JobControl):
    def __init__(self, parent_flow, securitytoken, job_name_prefix, max_tries, job_name, params, warn_only, report_interval, secret_params_re, allow_missing_jobs):
        for key, value in params.iteritems():
            # Handle parameters passed as int or bool. Booleans will be lowercased!
            if isinstance(value, (bool, int)):
                params[key] = str(value).lower()
        self.params = params
        super(_SingleJob, self).__init__(parent_flow, securitytoken, max_tries, warn_only, report_interval, secret_params_re, allow_missing_jobs)
        self.job = None
        self.old_build = None
        self.name = job_name_prefix + job_name
        self.repr_str = self.name

        print(self.indentation + "job: ", self.name)

    def _prepare_first(self, require_job=False):
        self.api.poll()
        try:
            self.job = self.api.get_job(self.name)
        except Exception as ex:
            self.repr_str = repr(ex)
            if require_job or not self.allow_missing_jobs:
                raise MissingJobsException(self.job)
            print(self.indentation + "NOTE: ", self.repr_str)
            return

        self._prepare_to_invoke()

        # Build repr string with build-url with secret params replaced by '***'
        def build_query():
            query = [key + '=' + (value if not self.secret_params_re.search(key) else '******') for key, value in self.params.iteritems()]
            return '?' + '&'.join(query) if query else ''

        try:
            url = self.job.get_build_triggerurl(None, params=self.params)
            if isinstance(url, tuple):
                # Newer versions of jenkinsapi returns tuple (path, {args})
                # Insert ' - ' so that the build URL is not directly clickable, but will instead point to the job
                part1 = url[0].replace(self.job.name, self.job.name + ' - ')
                self.repr_str = part1 + build_query()
            else:
                # Older versions of jenkinsapi return real URL
                import urlparse
                up = urlparse.urlparse(self.job.get_build_triggerurl(None, params=self.params))
                # Insert ' - ' so that the build URL is not directly clickable, but will instead point to the job
                path = up.path.replace(self.job.name, self.job.name + ' - ')
                params = ';' + up.params if up.params else ''
                fragment = '#' + up.fragment if up.fragment else ''
                self.repr_str = repr(self.job.name) + ' ' + up.scheme + '://' + up.netloc + path + params + build_query() + fragment
        except TypeError:
            # Current Jenkins!
            # Newer version take no args for get_build_triggerurl
            url = self.job.get_build_triggerurl()
            # Even Newer versions of jenkinsapi returns basic path without any args
            # Insert ' - ' so that the build URL is not directly clickable, but will instead point to the job
            part1 = url.replace(self.job.name, self.job.name + ' - ')
            self.repr_str = part1 + build_query()

        print(self.indentation + "job: ", end='')
        self._print_status_message(self.old_build)


    def __repr__(self):
        return self.repr_str

    def _print_status_message(self, build):
        state = "RUNNING" if self.job.is_running() else ("QUEUED" if self.job.is_queued() else "IDLE")
        print(repr(self.job.name), "Status", state, "- latest build:", '#' + str(build.buildno) if build else None)

    def _prepare_to_invoke(self):
        super(_SingleJob, self)._prepare_to_invoke()
        self.job.poll()
        self.old_build = self.job.get_last_build_or_none()

    def _check(self, start_time, last_report_time):
        if not self._invoke_if_not_invoked():
            if self.job is None:
                self._prepare_first(require_job=True)
            try:
                self.job.invoke(securitytoken=self.securitytoken, invoke_pre_check_delay=0, block=False, build_params=self.params if self.params else None)
            except TypeError as ex:
                # Older version of jenkinsapi
                self.job.invoke(securitytoken=self.securitytoken, invoke_pre_check_delay=0, block=False, params=self.params if self.params else None)

        self.job.poll()
        for _ in range(1, 20):
            try:
                build = self.job.get_last_build_or_none()
            except KeyError as ex:
                # Workaround for jenkinsapi timing dependency
                print("'get_last_build_or_none' failed: " + str(ex) + ", retrying.")
                time.sleep(0.1)

        if build == None:
            return last_report_time

        old_buildno = (self.old_build.buildno if self.old_build else None)
        if build.buildno == old_buildno or build.is_running():
            now = time.time()
            if now - last_report_time >= self.report_interval:
                self._print_status_message(build)
                last_report_time = now
            return last_report_time

        # The job has stopped running
        self._print_status_message(build)
        url = build.get_result_url().replace('testReport/api/python', 'console')
        print(str(build.get_status()) + ":", repr(self.job.name), "- build:", url, self._time_msg(start_time))

        self.result = self._jenkins_result_to_result(build.get_status())
        if self.result in (self.RESULT_SUCCESS, self.RESULT_UNSTABLE):
            return last_report_time

        raise FailedSingleJobException(self.job, self.warn_only)

    def sequence(self):
        return self.name


class _IgnoredSingleJob(_SingleJob):
    def __init__(self, parent_flow, securitytoken, job_name_prefix, job_name, params, report_interval, secret_params_re, allow_missing_jobs):
        super(_IgnoredSingleJob, self).__init__(parent_flow, securitytoken, job_name_prefix, 1, job_name, params, True, report_interval, secret_params_re, allow_missing_jobs)

    def _prepare_to_invoke(self):
        if self.tried_times < self.max_tries:
            super(_IgnoredSingleJob, self)._prepare_to_invoke()

    def _check(self, start_time, last_report_time):
        try:
            return super(_IgnoredSingleJob, self)._check(start_time, last_report_time)
        except FailedSingleJobException:
            return last_report_time
        finally:
            self.result = self.RESULT_UNCHECKED


# Retries are handled in the _Flow classes instead of _SingleJob since the individual jobs don't know
# how to retry. The _Serial flow is retried from start of flow and in _Parallel flow individual jobs
# are retried immediately

class _Flow(_JobControl):
    __metaclass__ = abc.ABCMeta

    def __init__(self, parent_flow, timeout, securitytoken, job_name_prefix, max_tries, warn_only, report_interval, secret_params, allow_missing_jobs):
        secret_params_re = re.compile(secret_params) if isinstance(secret_params, str) else secret_params
        super(_Flow, self).__init__(parent_flow, securitytoken, max_tries, warn_only, report_interval, secret_params_re, allow_missing_jobs)
        self.timeout = timeout
        self.job_name_prefix = self.parent_flow.job_name_prefix + job_name_prefix
        self.jobs = []

    def parallel(self, timeout=0, securitytoken=None, job_name_prefix='', max_tries=1, warn_only=False, report_interval=None, secret_params=None, allow_missing_jobs=None):
        return _Parallel(self, timeout, securitytoken, job_name_prefix, max_tries, warn_only, report_interval, secret_params, allow_missing_jobs)

    def serial(self, timeout=0, securitytoken=None, job_name_prefix='', max_tries=1, warn_only=False, report_interval=None, secret_params=None, allow_missing_jobs=None):
        return _Serial(self, timeout, securitytoken, job_name_prefix, max_tries, warn_only, report_interval, secret_params, allow_missing_jobs)

    def invoke(self, job_name, **params):
        job = _SingleJob(self, self.securitytoken, self.job_name_prefix, self.max_tries, job_name, params, self.warn_only,
                         self.report_interval, self.secret_params_re, self.allow_missing_jobs)
        self.jobs.append(job)

    def invoke_unchecked(self, job_name, **params):
        job = _IgnoredSingleJob(self, self.securitytoken, self.job_name_prefix, job_name, params, self.report_interval, self.secret_params_re, self.allow_missing_jobs)
        self.jobs.append(job)

    def _check_timeout(self, start_time):
        now = time.time()
        if self.timeout and now - self.invocation_time > self.timeout:
            unfinished_msg = "Unfinished jobs:" + str(self)
            raise FlowTimeoutException("Timeout after:" + self._time_msg(start_time) + unfinished_msg, self.warn_only)

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


class _Parallel(_Flow):
    def __init__(self, parent_flow, timeout, securitytoken, job_name_prefix='', max_tries=1, warn_only=False,
                 report_interval=None, secret_params=_default_secret_params_re, allow_missing_jobs=None):
        super(_Parallel, self).__init__(parent_flow, timeout, securitytoken, job_name_prefix, max_tries, warn_only,
                                        report_interval, secret_params, allow_missing_jobs)
        self._failed_child_jobs = {}

    def _prepare_first(self):
        print(self.indentation + "parallel flow: (")
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

    def _check(self, start_time, last_report_time):
        self._invoke_if_not_invoked()
        self._check_timeout(start_time)

        finished = True
        for job in self.jobs:
            if job.result or job.total_tried_times == job.total_max_tries:
                continue

            try:
                last_report_time = job._check(start_time, last_report_time)
                if not job.result:
                    finished = False
                    continue
                if id(job) in self._failed_child_jobs:
                    del self._failed_child_jobs[id(job)]
            except JobControlFailException:
                self._failed_child_jobs[id(job)] = job
                job.tried_times += 1
                job.total_tried_times += 1

                if job.tried_times < job.max_tries:
                    print("RETRY:", job, "failed but will be retried. Up to", job.max_tries - job.tried_times, "more times in current flow")
                    job._prepare_to_invoke()
                    continue

                if job.total_tried_times < job.total_max_tries:
                    print("RETRY:", job, "failed but will be retried. Up to", job.total_max_tries - job.total_tried_times, "more times through outer flow")
                    job._prepare_to_invoke()
                    job.tried_times = 0

        if finished:
            # All jobs have stopped running
            self.result = self.RESULT_SUCCESS
            for job in self.jobs:
                self.result = min(self.result, job.result if not (job.warn_only and job.result == self.RESULT_FAIL) else self.RESULT_UNSTABLE)

            if self.result == self.RESULT_FAIL:
                print("FAILURE:", self, self._time_msg(start_time))
                raise FailedChildJobsException(self, self._failed_child_jobs.values(), self.warn_only)

            if self.result == self.RESULT_SUCCESS:
                print("SUCCESS:", self, self._time_msg(start_time))

            if self.result == self.RESULT_UNSTABLE:
                print("UNSTABLE:", self, self._time_msg(start_time))

        return last_report_time

    def sequence(self):
        return tuple([job.sequence() for job in self.jobs])


class _Serial(_Flow):
    def __init__(self, parent_flow, securitytoken, timeout, job_name_prefix='', max_tries=1, warn_only=False,
                 report_interval=None, secret_params=_default_secret_params_re, allow_missing_jobs=None):
        super(_Serial, self).__init__(parent_flow, securitytoken, timeout, job_name_prefix, max_tries, warn_only,
                                      report_interval, secret_params, allow_missing_jobs)
        self.job_index = 0
        self.has_warning = False

    def _prepare_first(self):
        print(self.indentation + "serial flow: [")
        for job in self.jobs:
            job._prepare_first()
        print(self.indentation + "]\n")

    def _prepare_to_invoke(self):
        super(_Serial, self)._prepare_to_invoke()
        self.job_index = 0

    def __enter__(self):
        print(self.indentation + "serial flow: [")
        super(_Serial, self).__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        print(self.indentation + "]")
        super(_Serial, self).__exit__(exc_type, exc_value, traceback)
        print()

    def _check(self, start_time, last_report_time):
        self._invoke_if_not_invoked()
        self._check_timeout(start_time)

        job = self.jobs[self.job_index]
        try:
            last_report_time = job._check(start_time, last_report_time)
            if not job.result:
                return last_report_time
        except JobControlFailException:
            # The job has stopped running
            num_fail = self.job_index
            self.job_index = 0
            job.tried_times += 1
            job.total_tried_times += 1

            if job.tried_times < job.max_tries:
                print("RETRY:", job, "failed, retrying child jobs from beginning. Up to", job.max_tries - job.tried_times, "more times in current flow")
                for pre_job in self.jobs[0:num_fail]:
                    pre_job._prepare_to_invoke()
                    pre_job.tried_times += 1
                    pre_job.total_tried_times += 1
                return last_report_time

            if job.total_tried_times < job.total_max_tries:
                print("RETRY:", job, "failed, retrying child jobs from beginning. Up to", job.total_max_tries - job.total_tried_times, "more times through outermost flow")
                job.tried_times = 0
                for pre_job in self.jobs[0:num_fail]:
                    pre_job._prepare_to_invoke()
                    pre_job.tried_times = 0
                    pre_job.total_tried_times += 1

            if not self.warn_only:
                print("FAILURE:", self, self._time_msg(start_time))
                self.result = self.RESULT_FAIL
                raise FailedChildJobException(self, job, self.warn_only)

            self.has_warning = True
            self.job_index = len(self.jobs) - 1

        self.job_index += 1

        if self.job_index == len(self.jobs):
            # Check if any of the jobs is in warning or we have warning set ourself
            self.result = self.RESULT_UNSTABLE if self.has_warning else self.RESULT_SUCCESS
            for job in self.jobs:
                self.result = min(self.result, job.result if not (job.warn_only and job.result == self.RESULT_FAIL) else self.RESULT_UNSTABLE)

            if self.result == self.RESULT_SUCCESS:
                print("SUCCESS:", self, self._time_msg(start_time))

            if self.result == self.RESULT_UNSTABLE:
                print("UNSTABLE:", self, self._time_msg(start_time))

        return last_report_time

    def sequence(self):
        return [job.sequence() for job in self.jobs]


class _TopLevelControllerMixin(object):
    __metaclass__ = abc.ABCMeta

    def toplevel_init(self, jenkins_api, securitytoken, username, password):
        self._start_msg()
        # pylint: disable=attribute-defined-outside-init
        self.parent_flow = self
        self.top_flow = self
        self.job_name_prefix = ''
        self.total_max_tries = 1
        self.nesting_level = -1
        self.current_nesting_level = -1
        self.securitytoken = None
        self.report_interval = _default_report_interval
        self.secret_params_re = _default_secret_params_re
        self.allow_missing_jobs = None

        self._api = jenkins_api
        self.username = username
        self.password = password
        return securitytoken or jenkins_api.securitytoken if hasattr(jenkins_api, 'securitytoken') else None

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

        # Wait for jobs to finish
        print()
        print("--- Getting initial job status ---")
        self._prepare_first()

        mocked = os.environ.get('JENKINSFLOW_MOCK_API')
        sleep_time = 0.01 if mocked else 0.5
        last_report_time = start_time = time.time()

        print()
        print("--- Starting flow ---")
        while not self.result:
            last_report_time = self._check(start_time, last_report_time)
            time.sleep(min(sleep_time, self.report_interval))

        if self.result == self.RESULT_UNSTABLE:
            set_build_result(self.username, self.password, 'unstable')


class parallel(_Parallel, _TopLevelControllerMixin):
    def __init__(self, jenkins_api, timeout, securitytoken=None, username=None, password=None, job_name_prefix='', max_tries=1, warn_only=False,
                 report_interval=_default_report_interval, secret_params=_default_secret_params_re, allow_missing_jobs=False):
        """warn_only: causes failure in this job not to fail the parent flow"""
        securitytoken = self.toplevel_init(jenkins_api, securitytoken, username, password)
        super(parallel, self).__init__(self, timeout, securitytoken, job_name_prefix, max_tries, warn_only, report_interval, secret_params, allow_missing_jobs)
        self.parent_flow = None

    def __exit__(self, exc_type, exc_value, traceback):
        super(parallel, self).__exit__(exc_type, exc_value, traceback)
        self.wait_for_jobs()


class serial(_Serial, _TopLevelControllerMixin):
    def __init__(self, jenkins_api, timeout, securitytoken=None, username=None, password=None, job_name_prefix='', max_tries=1, warn_only=False,
                 report_interval=_default_report_interval, secret_params=_default_secret_params_re, allow_missing_jobs=False):
        """warn_only: causes failure in this job not to fail the parent flow"""
        securitytoken = self.toplevel_init(jenkins_api, securitytoken, username, password)
        super(serial, self).__init__(self, timeout, securitytoken, job_name_prefix, max_tries, warn_only, report_interval, secret_params, allow_missing_jobs)
        self.parent_flow = None

    def __exit__(self, exc_type, exc_value, traceback):
        super(serial, self).__exit__(exc_type, exc_value, traceback)
        self.wait_for_jobs()
