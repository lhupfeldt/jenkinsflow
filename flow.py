# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

import os, time, re, abc
from os.path import join as jp
from enum import IntEnum, Enum
from collections import OrderedDict

from set_build_result import set_build_result

_default_poll_interval = 0.5
_default_report_interval = 5
_default_secret_params = '.*passw.*|.*PASSW.*'
_default_secret_params_re = re.compile(_default_secret_params)


_hyperspeed_speedup = 1 if os.environ.get('JENKINSFLOW_MOCK_API') != 'true' else 500
def hyperspeed_time():
    return time.time() * _hyperspeed_speedup


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
    def __init__(self, job_name):
        msg = "Could not get job info for: " + repr(job_name)
        super(MissingJobsException, self).__init__(msg, warn_only=False)


class FailedChildJobException(JobControlFailException):
    def __init__(self, flow_job, failed_child_job, warn_only):
        msg = "Failed child job in: " + repr(flow_job) + ", child job:" + repr(failed_child_job) + ", warn_only:" + str(warn_only)
        super(FailedChildJobException, self).__init__(msg, warn_only)


class FailedChildJobsException(JobControlFailException):
    def __init__(self, flow_job, failed_child_jobs, warn_only):
        msg = "Failed child jobs in: " + repr(flow_job) + ", child jobs:" + repr(failed_child_jobs) + ", warn_only:" + str(warn_only)
        super(FailedChildJobsException, self).__init__(msg, warn_only)


class BuildResult(IntEnum):
    # pylint: disable=no-init
    FAILURE = 0
    UNSTABLE = 1
    UNCHECKED = 2
    SUCCESS = 3

    # Jenkins Aliases?
    PASSED = 3
    FAILED = 0


class BuildProgressState(Enum):
    # pylint: disable=no-init
    RUNNING = 0
    QUEUED = 1
    IDLE = 2


class _JobControl(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, parent_flow, securitytoken, max_tries, warn_only, secret_params_re, allow_missing_jobs):
        self.parent_flow = parent_flow
        self.top_flow = parent_flow.top_flow

        self.max_tries = max_tries
        self.total_max_tries = self.max_tries * self.parent_flow.total_max_tries

        self.nesting_level = self.parent_flow.nesting_level + 1
        if self.nesting_level != self.top_flow.current_nesting_level + 1:
            raise FlowScopeException("Flow used out of scope")

        self.securitytoken = securitytoken or self.parent_flow.securitytoken
        self.warn_only = warn_only
        self.secret_params_re = secret_params_re or self.parent_flow.secret_params_re
        self.allow_missing_jobs = allow_missing_jobs if allow_missing_jobs is not None else self.parent_flow.allow_missing_jobs

        self.result = BuildResult.FAILURE
        self.tried_times = 0
        self.total_tried_times = 0
        self.invocation_time = None

        self.node_id = self.top_flow._next_node_id
        self.top_flow._next_node_id += 1

    def __enter__(self):
        self.top_flow.current_nesting_level += 1

    def __exit__(self, exc_type, exc_value, traceback):
        self.top_flow.current_nesting_level -= 1

    @abc.abstractmethod
    def _prepare_first(self):
        raise Exception("AbstractNotImplemented")

    def _prepare_to_invoke(self):
        """Must be called before each invocation of a job, as opposed to __init__, which is called once in entire run"""
        self.invocation_time = 0

    def _invoke_if_not_invoked(self):
        if self.invocation_time:
            return True

        self.invocation_time = hyperspeed_time()
        print("\nInvoking (%d/%d,%d/%d):" % (self.tried_times + 1, self.max_tries, self.total_tried_times + 1, self.total_max_tries), self)
        return False

    @abc.abstractmethod
    def _check(self, report_now):
        """Polled by flow controller until the job reaches state 'successful' or tried_times == parent.max_tries * self.max_tries"""
        raise Exception("AbstractNotImplemented")

    def _time_msg(self):
        now = hyperspeed_time()
        return "after: %.3fs/%.3fs" % (now - self.invocation_time, now - self.top_flow.start_time)

    @abc.abstractmethod
    def sequence(self):
        raise Exception("AbstractNotImplemented")

    @property
    def indentation(self):
        return self.nesting_level * 3 * ' '

    @property
    def api(self):
        return self.top_flow._api

    def __repr__(self):
        return str(self.sequence())

    @abc.abstractmethod
    def last_jobs_in_flow(self):
        """For json graph calculation"""
        raise Exception("AbstractNotImplemented")

    @abc.abstractmethod
    def links_and_nodes(self, prev_jobs, node_to_id):
        """For json graph calculation"""
        raise Exception("AbstractNotImplemented")


class _SingleJob(_JobControl):
    def __init__(self, parent_flow, securitytoken, job_name_prefix, max_tries, job_name, params, warn_only, secret_params_re, allow_missing_jobs):
        for key, value in params.iteritems():
            # Handle parameters passed as int or bool. Booleans will be lowercased!
            if isinstance(value, (bool, int)):
                params[key] = str(value).lower()
        self.params = params
        super(_SingleJob, self).__init__(parent_flow, securitytoken, max_tries, warn_only, secret_params_re, allow_missing_jobs)
        # There is no separate retry for individual jobs, so set self.total_max_tries to the same as parent flow!
        self.total_max_tries = self.parent_flow.total_max_tries
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
            # TODO? stack trace
            self.repr_str = repr(ex)
            if require_job or not self.allow_missing_jobs:
                raise MissingJobsException(self.name)
            print(self.indentation + "NOTE: ", self.repr_str)
            return

        self._prepare_to_invoke()

        # Build repr string with build-url with secret params replaced by '***'
        def build_query():
            query = [key + '=' + (value if not self.secret_params_re.search(key) else '******') for key, value in self.params.iteritems()]
            return '?' + '&'.join(query) if query else ''

        try:  # This is for support of old jenkinsapi version, not tested
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
        state = BuildProgressState.RUNNING if self.job.is_running() else BuildProgressState.QUEUED if self.job.is_queued() else BuildProgressState.IDLE
        print(repr(self.job.name), "Status", state.name, "- latest build:", '#' + str(build.buildno) if build else None)

    def _prepare_to_invoke(self):
        super(_SingleJob, self)._prepare_to_invoke()
        self.job.poll()
        self.old_build = self.job.get_last_build_or_none()
        self.result = BuildResult.FAILED

    def _check(self, report_now):
        if not self._invoke_if_not_invoked():
            if self.job is None:
                self._prepare_first(require_job=True)

            build_params = self.params if self.params else None
            try:
                self.job.invoke(securitytoken=self.securitytoken, invoke_pre_check_delay=0, block=False, build_params=build_params, cause=self.top_flow.cause)
            except TypeError as ex:  # Old version of jenkinsapi
                try:
                    self.job.invoke(securitytoken=self.securitytoken, invoke_pre_check_delay=0, block=False, params=build_params, cause=self.top_flow.cause)
                except TypeError:  # Not the old version after all? reraise originalexception
                    # TODO stacktrace of second exception
                    raise ex

        for _ in range(1, 20):
            self.job.poll()
            try:
                build = self.job.get_last_build_or_none()
                break
            except KeyError as ex:  # pragma: no cover
                # Workaround for jenkinsapi timing dependency?
                print("'get_last_build_or_none' failed: " + str(ex) + ", retrying.")
                time.sleep(0.1 / _hyperspeed_speedup)

        old_buildno = (self.old_build.buildno if self.old_build else None)
        if build is None or build.buildno == old_buildno or build.is_running():
            if report_now:
                self._print_status_message(build)
            return

        # The job has stopped running
        self._print_status_message(build)
        self.result = BuildResult[build.get_status()]
        url = build.get_result_url().replace('testReport/api/python', 'console')
        print(str(build.get_status()) + ":", repr(self.job.name), "- build:", url, self._time_msg())

        if self.result not in (BuildResult.SUCCESS, BuildResult.UNSTABLE):
            raise FailedSingleJobException(self.job, self.warn_only)

    def sequence(self):
        return self.name

    def last_jobs_in_flow(self):
        return [self]

    def links_and_nodes(self, prev_jobs, node_to_id):
        node_id = node_to_id(self)
        node_name = self.name[self.top_flow.json_strip_index:]
        url = self.job.baseurl if self.job is not None else None
        node = OrderedDict((("id", node_id), ("name", node_name), ("url", url)))
        links = []
        for job in prev_jobs:
            links.append(OrderedDict((("source", node_to_id(job)), ("target", node_id))))

        return [node], links



class _IgnoredSingleJob(_SingleJob):
    def __init__(self, parent_flow, securitytoken, job_name_prefix, job_name, params, secret_params_re, allow_missing_jobs):
        super(_IgnoredSingleJob, self).__init__(parent_flow, securitytoken, job_name_prefix, 1, job_name, params, True, secret_params_re, allow_missing_jobs)

    def _prepare_to_invoke(self):
        if self.tried_times < self.max_tries:
            super(_IgnoredSingleJob, self)._prepare_to_invoke()

    def _check(self, report_now):
        try:
            super(_IgnoredSingleJob, self)._check(report_now)
        except FailedSingleJobException:
            pass
        finally:
            self.result = BuildResult.UNCHECKED


# Retries are handled in the _Flow classes instead of _SingleJob since the individual jobs don't know
# how to retry. The _Serial flow is retried from start of flow and in _Parallel flow individual jobs
# are retried immediately

class _Flow(_JobControl):
    __metaclass__ = abc.ABCMeta

    def __init__(self, parent_flow, timeout, securitytoken, job_name_prefix, max_tries, warn_only, report_interval, secret_params, allow_missing_jobs):
        secret_params_re = re.compile(secret_params) if isinstance(secret_params, str) else secret_params
        super(_Flow, self).__init__(parent_flow, securitytoken, max_tries, warn_only, secret_params_re, allow_missing_jobs)
        self.timeout = timeout
        self.job_name_prefix = self.parent_flow.job_name_prefix + job_name_prefix
        self.report_interval = report_interval or self.parent_flow.report_interval

        self.jobs = []
        self.last_report_time = 0

    def parallel(self, timeout=0, securitytoken=None, job_name_prefix='', max_tries=1, warn_only=False, report_interval=None, secret_params=None, allow_missing_jobs=None):
        return _Parallel(self, timeout, securitytoken, job_name_prefix, max_tries, warn_only, report_interval, secret_params, allow_missing_jobs)

    def serial(self, timeout=0, securitytoken=None, job_name_prefix='', max_tries=1, warn_only=False, report_interval=None, secret_params=None, allow_missing_jobs=None):
        return _Serial(self, timeout, securitytoken, job_name_prefix, max_tries, warn_only, report_interval, secret_params, allow_missing_jobs)

    def invoke(self, job_name, **params):
        job = _SingleJob(self, self.securitytoken, self.job_name_prefix, self.max_tries, job_name, params, self.warn_only, self.secret_params_re, self.allow_missing_jobs)
        self.jobs.append(job)

    def invoke_unchecked(self, job_name, **params):
        job = _IgnoredSingleJob(self, self.securitytoken, self.job_name_prefix, job_name, params, self.secret_params_re, self.allow_missing_jobs)
        self.jobs.append(job)

    def _check_timeout(self):
        now = hyperspeed_time()
        if self.timeout and now - self.invocation_time > self.timeout:
            # TODO: These are not the unfinished jobs!
            unfinished_msg = ". Unfinished jobs:" + str(self)
            raise FlowTimeoutException("Timeout after:" + self._time_msg() + unfinished_msg, self.warn_only)

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

    def _check_invoke_timeout_report(self):
        self._invoke_if_not_invoked()
        self._check_timeout()

        now = hyperspeed_time()
        report_now = now - self.last_report_time >= self.report_interval
        if report_now:
            self.last_report_time = now
        return report_now

    def json(self, file_path, indent=None):
        node_to_id = lambda job : job.node_id
        if indent:
            node_to_id = lambda job : job.name

        nodes, links = self.links_and_nodes([], node_to_id)
        graph = {'nodes': nodes, 'links': links}

        import json
        from atomicfile import AtomicFile
        if file_path is not None:
            with AtomicFile(file_path, 'w+') as out_file:
                json.dump(graph, out_file, indent=indent)
        else:
            return json.dumps(graph, indent=indent)


class _Parallel(_Flow):
    def __init__(self, parent_flow, timeout, securitytoken, job_name_prefix='', max_tries=1, warn_only=False,
                 report_interval=None, secret_params=_default_secret_params_re, allow_missing_jobs=None):
        super(_Parallel, self).__init__(parent_flow, timeout, securitytoken, job_name_prefix, max_tries, warn_only,
                                        report_interval, secret_params, allow_missing_jobs)
        self._failed_child_jobs = {}

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
        report_now = self._check_invoke_timeout_report()

        finished = True
        for job in self.jobs:
            if job.result or job.total_tried_times == job.total_max_tries:
                continue

            try:
                job._check(report_now)
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
                    finished = False
                    job._prepare_to_invoke()
                    continue

                if job.total_tried_times < job.total_max_tries:
                    print("RETRY:", job, "failed but will be retried. Up to", job.total_max_tries - job.total_tried_times, "more times through outer flow")
                    job._prepare_to_invoke()
                    job.tried_times = 0
                    continue

        if finished:
            # All jobs have stopped running
            self.result = BuildResult.SUCCESS
            for job in self.jobs:
                self.result = min(self.result, job.result if not (job.warn_only and job.result == BuildResult.FAILURE) else BuildResult.UNSTABLE)
            print(self.result.name, self, self._time_msg())

            if self.result == BuildResult.FAILURE:
                raise FailedChildJobsException(self, self._failed_child_jobs.values(), self.warn_only)

    def sequence(self):
        return tuple([job.sequence() for job in self.jobs])

    def last_jobs_in_flow(self):
        jobs = []
        for job in self.jobs:
            jobs.extend(job.last_jobs_in_flow())
        return jobs

    def links_and_nodes(self, prev_jobs, node_to_id):
        nodes = []
        links = []
        for job in self.jobs:
            child_nodes, child_links = job.links_and_nodes(prev_jobs, node_to_id)
            nodes.extend(child_nodes)
            links.extend(child_links)
        return nodes, links


class _Serial(_Flow):
    def __init__(self, parent_flow, securitytoken, timeout, job_name_prefix='', max_tries=1, warn_only=False,
                 report_interval=None, secret_params=_default_secret_params_re, allow_missing_jobs=None):
        super(_Serial, self).__init__(parent_flow, securitytoken, timeout, job_name_prefix, max_tries, warn_only,
                                      report_interval, secret_params, allow_missing_jobs)
        self.job_index = 0
        self.has_warning = False

    def _prepare_first(self):
        print(self.indentation + "serial flow: [")
        self._prepare_to_invoke()
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

    def _check(self, report_now):
        report_now = self._check_invoke_timeout_report()

        job = self.jobs[self.job_index]
        try:
            job._check(report_now)
            if not job.result:
                return
        except JobControlFailException:
            # The job has stopped running
            num_fail = self.job_index
            self.job_index = 0
            job.tried_times += 1
            job.total_tried_times += 1

            if job.tried_times < job.max_tries:
                print("RETRY:", job, "failed, retrying child jobs from beginning. Up to", job.max_tries - job.tried_times, "more times in current flow")
                job._prepare_to_invoke()
                for pre_job in self.jobs[0:num_fail]:
                    pre_job._prepare_to_invoke()
                    pre_job.tried_times += 1
                    pre_job.total_tried_times += 1
                return

            if job.total_tried_times < job.total_max_tries:
                print("RETRY:", job, "failed, retrying child jobs from beginning. Up to", job.total_max_tries - job.total_tried_times, "more times through outer flow")
                job._prepare_to_invoke()
                job.tried_times = 0
                for pre_job in self.jobs[0:num_fail]:
                    pre_job._prepare_to_invoke()
                    pre_job.tried_times = 0
                    pre_job.total_tried_times += 1

            if not self.warn_only:
                self.result = BuildResult.FAILURE
                print(self.result.name, self, self._time_msg())
                raise FailedChildJobException(self, job, self.warn_only)

            # All retries are exhausted
            self.has_warning = True
            self.job_index = len(self.jobs) - 1

        self.job_index += 1

        if self.job_index == len(self.jobs):
            # Check if any of the jobs is in warning or we have warning set ourself
            self.result = BuildResult.UNSTABLE if self.has_warning else BuildResult.SUCCESS
            for job in self.jobs:
                self.result = min(self.result, job.result if not (job.warn_only and job.result == BuildResult.FAILURE) else BuildResult.UNSTABLE)
            print(self.result.name, self, self._time_msg())

    def sequence(self):
        return [job.sequence() for job in self.jobs]

    def last_jobs_in_flow(self):
        return self.jobs[-1].last_jobs_in_flow()

    def links_and_nodes(self, prev_jobs, node_to_id):
        nodes = []
        links = []
        for job in self.jobs:
            child_nodes, child_links = job.links_and_nodes(prev_jobs, node_to_id)
            nodes.extend(child_nodes)
            links.extend(child_links)
            prev_jobs = job.last_jobs_in_flow()
        return nodes, links


class _TopLevelControllerMixin(object):
    __metaclass__ = abc.ABCMeta

    def toplevel_init(self, jenkins_api, securitytoken, username, password, top_level_job_name_prefix, poll_interval, json_dir, json_indent, json_strip_top_level_prefix):
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
        self._next_node_id = 0

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

        self.json_dir = json_dir
        self.json_indent = json_indent
        self.json_strip_index = len(top_level_job_name_prefix) if json_strip_top_level_prefix else 0
        self.json_file = jp(self.json_dir, 'flow_graph.json') if json_dir is not None else None

        # Allow test framework to set securitytoken, that we won't have to litter all the testcases with it
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
        self._prepare_first()

        if self.json_file:
            self.json(self.json_file, self.json_indent)

        # pylint: disable=attribute-defined-outside-init
        self.start_time = hyperspeed_time()
        self.last_report_time = self.start_time

        print()
        print("--- Starting flow ---")
        sleep_time = float(min(self.poll_interval, self.report_interval)) / _hyperspeed_speedup
        while not self.result:
            self._check(None)
            time.sleep(sleep_time)

        if self.result == BuildResult.UNSTABLE:
            set_build_result(self.username, self.password, 'unstable')


class parallel(_Parallel, _TopLevelControllerMixin):
    def __init__(self, jenkins_api, timeout, securitytoken=None, username=None, password=None, job_name_prefix='', max_tries=1, warn_only=False,
                 report_interval=_default_report_interval, poll_interval=_default_poll_interval, secret_params=_default_secret_params_re, allow_missing_jobs=False,
                 json_dir=None, json_indent=None, json_strip_top_level_prefix=True):
        """warn_only: causes failure in this job not to fail the parent flow"""
        securitytoken = self.toplevel_init(jenkins_api, securitytoken, username, password, job_name_prefix, poll_interval,
                                           json_dir, json_indent, json_strip_top_level_prefix)
        super(parallel, self).__init__(self, timeout, securitytoken, job_name_prefix, max_tries, warn_only, report_interval, secret_params, allow_missing_jobs)
        self.parent_flow = None

    def __exit__(self, exc_type, exc_value, traceback):
        super(parallel, self).__exit__(exc_type, exc_value, traceback)
        self.wait_for_jobs()


class serial(_Serial, _TopLevelControllerMixin):
    def __init__(self, jenkins_api, timeout, securitytoken=None, username=None, password=None, job_name_prefix='', max_tries=1, warn_only=False,
                 report_interval=_default_report_interval, poll_interval=_default_poll_interval, secret_params=_default_secret_params_re, allow_missing_jobs=False,
                 json_dir=None, json_indent=None, json_strip_top_level_prefix=True):
        """warn_only: causes failure in this job not to fail the parent flow"""
        securitytoken = self.toplevel_init(jenkins_api, securitytoken, username, password, job_name_prefix, poll_interval,
                                           json_dir, json_indent, json_strip_top_level_prefix)
        super(serial, self).__init__(self, timeout, securitytoken, job_name_prefix, max_tries, warn_only, report_interval, secret_params, allow_missing_jobs)
        self.parent_flow = None

    def __exit__(self, exc_type, exc_value, traceback):
        super(serial, self).__exit__(exc_type, exc_value, traceback)
        self.wait_for_jobs()
