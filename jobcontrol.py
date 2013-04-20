# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import time, re, abc, urlparse

_default_report_interval = 5
_default_secret_params = '.*passw.*|.*PASSW.*'
_default_secret_params_re = re.compile(_default_secret_params)

_debug = False

class JobControlException(Exception):
    pass


class FlowTimeoutException(JobControlException):
    pass


class JobControlFailException(JobControlException):
    __metaclass__ = abc.ABCMeta


class FailedSingleJobException(JobControlFailException):
    def __init__(self, job):
        msg = "Failed job: " + repr(job)
        super(FailedSingleJobException, self).__init__(msg)


class FailedChildJobException(JobControlFailException):
    def __init__(self, flow_job, failed_child_job):
        msg = "Failed child job in: " + repr(flow_job) + ", child job:" + repr(failed_child_job)
        super(FailedChildJobException, self).__init__(msg)


class FailedChildJobsException(JobControlFailException):
    def __init__(self, flow_job, failed_child_jobs):
        msg = "Failed child jobs in: " + repr(flow_job) + ", child jobs:" + repr(failed_child_jobs)
        super(FailedChildJobsException, self).__init__(msg)


class _JobControl(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, max_tries, parent_max_tries, report_interval, secret_params_re, nesting_level):
        self.max_tries = max_tries
        self.total_max_tries = self.max_tries * parent_max_tries
        self.report_interval = report_interval
        self.secret_params_re = secret_params_re
        self.nesting_level = nesting_level

        self.successful = False
        self.tried_times = 0
        self.total_tried_times = 0

        self._prepare_to_invoke(queuing=True)

    def _prepare_to_invoke(self, queuing=False):
        """Must be called before each invocation of a job, as opposed to __init__, which is called once in entire run"""
        self.invocation_time = 0

    def _invoke_if_not_invoked(self):
        if self.invocation_time:
            return True

        self.invocation_time = time.time()
        print "\nInvoking (%d/%d,%d/%d):" % (self.tried_times + 1, self.max_tries, self.total_tried_times + 1, self.total_max_tries), self
        return False

    @abc.abstractmethod
    def _check(self, start_time, last_report_time):
        """Polled by flow controller until the job reaches state 'successful' or tried_times == parent_max_tries * self.max_tries"""
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

    def __repr__(self):
        return str(self.sequence())

    def debug(self, *args):
        if not _debug:
            return
        print 'DEBUG in ' + self.__class__.__name__ + ':', ' '.join([str(arg) for arg in args])


class _SingleJob(_JobControl):
    def __init__(self, jenkins_api, job_name_prefix, max_tries, parent_max_tries, job_name, params, report_interval, secret_params_re, nesting_level):
        self.job = jenkins_api.get_job(job_name_prefix + job_name)
        self.params = params
        super(_SingleJob, self).__init__(max_tries, parent_max_tries, report_interval, secret_params_re, nesting_level)
        self.total_max_tries = parent_max_tries

        # Build repr string with build-url with secret params replaced by '***'
        # TODO: token instead of None?
        up = urlparse.urlparse(self.job.get_build_triggerurl(None, params=self.params))
        query = ''
        if up.query:
            query = [key + '=' + (value if not self.secret_params_re.search(key) else '******') for key, value in urlparse.parse_qsl(up.query)]
            query = '?' + '&'.join(query)
        # Insert ' - ' so that the build URL is not directly clickable, but will instead point to the job
        path = up.path.replace(self.job.name, self.job.name + ' - ')
        params = ';' + up.params if up.params else ''
        fragment = '#' + up.fragment if up.fragment else ''
        self.repr_str = repr(self.job.name) + ' ' + up.scheme + '://' + up.netloc + path + params + query + fragment

    def __repr__(self):
        return self.repr_str

    def _print_status_message(self, build):
        state = "RUNNING" if self.job.is_running() else ("QUEUED" if self.job.is_queued() else "IDLE")
        print repr(self.job.name), "Status", state, "- latest build:", build

    def _prepare_to_invoke(self, queuing=False):
        super(_SingleJob, self)._prepare_to_invoke(queuing)
        self.job.poll()
        self.old_build = self.job.get_last_build_or_none()
        if queuing:
            print self.indentation + "Queuing job:", self.job,
        self._print_status_message(self.old_build)

    def _check(self, start_time, last_report_time):
        if not self._invoke_if_not_invoked():
            self.job.invoke(invoke_pre_check_delay=0, block=False, params=self.params)

        self.job.poll()
        build = self.job.get_last_build_or_none()
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
        print str(build.get_status()) + ":", repr(self.job.name), "- build: ", build.get_result_url(), self._time_msg(start_time)

        if build.is_good():
            self.successful = True
            return last_report_time
        raise FailedSingleJobException(self.job)

    def sequence(self):
        return self.job.name


class _IgnoredSingleJob(_SingleJob):
    def __init__(self, jenkins_api, job_name_prefix, job_name, params, report_interval, secret_params_re, nesting_level):
        super(_IgnoredSingleJob, self).__init__(jenkins_api, job_name_prefix, 1, 1, job_name, params, report_interval, secret_params_re, nesting_level)

    def _prepare_to_invoke(self, queuing=False):
        if self.tried_times < self.max_tries:
            super(_IgnoredSingleJob, self)._prepare_to_invoke(queuing)

    def _check(self, start_time, last_report_time):
        try:
            return super(_IgnoredSingleJob, self)._check(start_time, last_report_time)
        except FailedSingleJobException:
            return last_report_time
        finally:
            self.successful = True


# Retries are handled in the _Flow classes instead of _SingleJob since the individual jobs don't know
# how to retry. The _Serial flow is retried from start of flow and in _Parallel flow individual jobs
# are retried immediately

class _Flow(_JobControl):
    __metaclass__ = abc.ABCMeta

    def __init__(self, jenkins_api, timeout, job_name_prefix, max_tries, parent_max_tries, report_interval, secret_params, nesting_level):
        secret_params_re = re.compile(secret_params) if isinstance(secret_params, str) else secret_params
        super(_Flow, self).__init__(max_tries, parent_max_tries, report_interval, secret_params_re, nesting_level)

        self.api = jenkins_api
        self.timeout = timeout
        self.job_name_prefix = job_name_prefix
        self.jobs = []

    def parallel(self, timeout=0, job_name_prefix='', max_tries=1, report_interval=None, secret_params=None):
        secret_params = secret_params or self.secret_params_re
        report_interval = report_interval or self.report_interval
        pll = _Parallel(self.api, timeout, self.job_name_prefix+job_name_prefix, max_tries, self.total_max_tries, report_interval, secret_params, self.nesting_level)
        self.jobs.append(pll)
        return pll

    def serial(self, timeout=0, job_name_prefix='', max_tries=1, report_interval=None, secret_params=None):
        secret_params = secret_params or self.secret_params_re
        report_interval = report_interval or self.report_interval
        ser = _Serial(self.api, timeout, self.job_name_prefix+job_name_prefix, max_tries, self.total_max_tries, report_interval, secret_params, self.nesting_level)
        self.jobs.append(ser)
        return ser

    def invoke(self, job_name, **params):
        job = _SingleJob(self.api, self.job_name_prefix, self.max_tries, self.total_max_tries, job_name, params, self.report_interval, self.secret_params_re, self.nesting_level)
        self.jobs.append(job)

    def invoke_unchecked(self, job_name, **params):
        job = _IgnoredSingleJob(self.api, self.job_name_prefix, job_name, params, self.report_interval, self.secret_params_re, self.nesting_level)
        self.jobs.append(job)

    def _check_timeout(self, start_time):
        now = time.time()
        if self.timeout and now - self.invocation_time > self.timeout:
            unfinished_msg = "Unfinished jobs:" + str(self)
            raise FlowTimeoutException("Timeout after:" + self._time_msg(start_time) + unfinished_msg)

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type:
            return None

        # Check for and remove empty flows
        new_job_list = []
        for job in self.jobs:
            if isinstance(job, _Flow):
                if not job.jobs:
                    print self.indentation + "INFO: Removing empty flow", job, "from: ", self
                    continue
            new_job_list.append(job)
        self.jobs = new_job_list


class _Parallel(_Flow):
    def __init__(self, jenkins_api, timeout, job_name_prefix='', max_tries=1, parent_max_tries=1, report_interval=None, secret_params=_default_secret_params_re, nesting_level=0):
        super(_Parallel, self).__init__(jenkins_api, timeout, job_name_prefix, max_tries, parent_max_tries, report_interval, secret_params, nesting_level)
        self._failed_child_jobs = {}

    def __enter__(self):
        print self.indentation + "Queuing jobs for parallel run: ("
        self.nesting_level += 1
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        super(_Parallel, self).__exit__(exc_type, exc_value, traceback)
        self.nesting_level -= 1
        print self.indentation + ")\n"

    def _check(self, start_time, last_report_time):
        self._invoke_if_not_invoked()
        self._check_timeout(start_time)

        finished = True
        for job in self.jobs:
            if job.successful or job.total_tried_times == job.total_max_tries:
                continue

            try:
                last_report_time = job._check(start_time, last_report_time)
                if not job.successful:
                    finished = False
                    continue
                if id(job) in self._failed_child_jobs:
                    del self._failed_child_jobs[id(job)]
            except JobControlFailException:
                self._failed_child_jobs[id(job)] = job
                job.tried_times += 1
                job.total_tried_times += 1

                if job.tried_times < job.max_tries:
                    print "RETRY:", job, "failed but will be retried. Up to", job.max_tries - job.tried_times, "more times in current flow"
                    job._prepare_to_invoke()
                    continue

                if job.total_tried_times < job.total_max_tries:
                    print "RETRY:", job, "failed but will be retried. Up to", job.total_max_tries - job.total_tried_times, "more times through outermost flow"
                    job._prepare_to_invoke()
                    job.tried_times = 0

        if finished:
            # All jobs have stopped running
            if self._failed_child_jobs:
                print "FAILURE:", self, self._time_msg(start_time)
                raise FailedChildJobsException(self, self._failed_child_jobs.values())
            print "SUCCESS:", self, self._time_msg(start_time)
            self.successful = True

        return last_report_time

    def sequence(self):
        return tuple([job.sequence() for job in self.jobs])


class _Serial(_Flow):
    def __init__(self, jenkins_api, timeout, job_name_prefix='', max_tries=1, parent_max_tries=1, report_interval=None, secret_params=_default_secret_params_re, nesting_level=0):
        super(_Serial, self).__init__(jenkins_api, timeout, job_name_prefix, max_tries, parent_max_tries, report_interval, secret_params, nesting_level)
        self.job_index = 0

    def _prepare_to_invoke(self, queuing=False):
        super(_Serial, self)._prepare_to_invoke(queuing)
        self.job_index = 0

    def __enter__(self):
        print self.indentation + "Queuing jobs for serial run: ["
        self.nesting_level += 1
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        super(_Serial, self).__exit__(exc_type, exc_value, traceback)
        self.nesting_level -= 1
        print self.indentation + "]\n"

    def _check(self, start_time, last_report_time):
        self._invoke_if_not_invoked()
        self._check_timeout(start_time)

        job = self.jobs[self.job_index]
        try:
            last_report_time = job._check(start_time, last_report_time)
            if not job.successful:
                return last_report_time
        except JobControlFailException:
            # The job has stopped running
            num_fail = self.job_index
            self.job_index = 0
            job.tried_times += 1
            job.total_tried_times += 1

            if job.tried_times < job.max_tries:
                print "RETRY:", job, "failed, retrying child jobs from beginning. Up to", job.max_tries - job.tried_times, "more times in current flow"
                for pre_job in self.jobs[0:num_fail]:
                    pre_job._prepare_to_invoke()
                    pre_job.tried_times += 1
                    pre_job.total_tried_times += 1
                return last_report_time

            if job.total_tried_times < job.total_max_tries:
                print "RETRY:", job, "failed, retrying child jobs from beginning. Up to", job.total_max_tries - job.total_tried_times, "more times through outermost flow"
                job.tried_times = 0
                for pre_job in self.jobs[0:num_fail]:
                    pre_job._prepare_to_invoke()
                    pre_job.tried_times = 0
                    pre_job.total_tried_times += 1

            print "FAILURE:", self, self._time_msg(start_time)
            raise FailedChildJobException(self, job)

        self.job_index += 1
        if self.job_index == len(self.jobs):
            print "SUCCESS:", self, self._time_msg(start_time)
            self.successful = True

        return last_report_time

    def sequence(self):
        return [job.sequence() for job in self.jobs]


class _TopLevelController(_Flow):
    def wait_for_jobs(self):
        if not self.jobs:
            print "WARNING: Empty toplevel flow", self, "nothing to do."
            return

        # Wait for jobs to finish
        print

        last_report_time = start_time = time.time()

        while not self.successful:
            last_report_time = self._check(start_time, last_report_time)
            time.sleep(min(0.5, self.report_interval))


def _start_msg():
    print "== Legend =="
    print "Serial builds: []"
    print "Parallel builds: ()"
    print "Invoking (w/x,y/z): w=current invocation in current flow scope, x=max in scope, y=total number of invocations, z=total max invocations"
    print "Elapsed time: 'after: x/y': x=time spent during current run of job, y=time elapsed since start of outermost flow"
    print ""


class parallel(_Parallel, _TopLevelController):
    def __init__(self, jenkins_api, timeout, job_name_prefix='', max_tries=1, report_interval=_default_report_interval, secret_params=_default_secret_params_re):
        _start_msg()
        super(parallel, self).__init__(jenkins_api, timeout, job_name_prefix, max_tries, 1, report_interval, secret_params, 0)

    def __exit__(self, exc_type, exc_value, traceback):
        super(parallel, self).__exit__(exc_type, exc_value, traceback)
        self.wait_for_jobs()


class serial(_Serial, _TopLevelController):
    def __init__(self, jenkins_api, timeout, job_name_prefix='', max_tries=1, report_interval=_default_report_interval, secret_params=_default_secret_params_re):
        _start_msg()
        super(serial, self).__init__(jenkins_api, timeout, job_name_prefix, max_tries, 1, report_interval, secret_params, 0)

    def __exit__(self, exc_type, exc_value, traceback):
        super(serial, self).__exit__(exc_type, exc_value, traceback)
        self.wait_for_jobs()
