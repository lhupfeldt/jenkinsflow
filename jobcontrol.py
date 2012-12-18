# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import time
import abc


class FlowTimeoutException(Exception):
    pass


class FailedJobsException(Exception):
    pass


def _print_status_message(job, build):
    print "Status", repr(job.name), "- running:", repr(job.is_running()) + ", queued:", job.is_queued(), "- latest build: ", build


def _nested_jobs(jobs):
    nested = jobs.jobs if isinstance(jobs, _Flow) else jobs
    nested = [(_nested_jobs(job) if isinstance(job, _Flow) else job.name) for job, _invoked, _params, _old_build in nested]
    if isinstance(jobs, _Parallel):
        return tuple(nested)
    return nested


def _check_job(job_details, report_interval, last_report_time):
    job, invoked, params, old_build = job_details

    if isinstance(job, _Flow):
        if not invoked:
            invoked = job_details[1] = time.time()
        return job._check_jobs(invoked, last_report_time)

    # job is a jenkins/hudson job
    if not invoked:
        print "Invoking:", repr(job.name)
        job_details[1] = time.time()
        job.invoke(invoke_pre_check_delay=0, block=False, params=params)

    job.poll()
    build = job.get_last_build_or_none()
    if build == None:
        return False, last_report_time, None

    old_buildno = (old_build.buildno if old_build else None)
    if build.buildno == old_buildno or build.is_running():
        now = time.time()
        if now - last_report_time >= report_interval:
            _print_status_message(job, build)
            last_report_time = now
        return False, last_report_time, None

    # The job has stopped running
    _print_status_message(job, build)
    failed = None
    if not build.is_good():
        failed = (job, params)
    print build.get_status(), ":", repr(job.name), "- build: ", build.get_result_url()

    return True, last_report_time, failed


class _Flow(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, jenkins_api, timeout, report_interval=5, job_name_prefix=''):
        self.api = jenkins_api
        self.timeout = timeout
        self.report_interval = report_interval
        self.job_name_prefix = job_name_prefix
        self.jobs = []

    def _get_job(self, job, params):
        if isinstance(job, str):
            job = self.api.get_job(self.job_name_prefix + job)
        old_build = job.get_last_build_or_none()
        self.jobs.append([job, False, params, old_build])
        _print_status_message(job, old_build)
        return job

    def parallel(self, timeout, report_interval=5, job_name_prefix=''):
        pll = _Parallel(self.api, timeout, report_interval, job_name_prefix=self.job_name_prefix+job_name_prefix)
        self.jobs.append([pll, False, None, None])
        return pll

    def serial(self, timeout, report_interval=5, job_name_prefix=''):
        ser = _Serial(self.api, timeout, report_interval, job_name_prefix=self.job_name_prefix+job_name_prefix)
        self.jobs.append([ser, False, None, None])
        return ser

    @abc.abstractmethod
    def _check_jobs(self, start_time, last_report_time):
        pass

    def _check_timeout(self, start_time):
        if not self.jobs:
            return

        now = time.time()
        if self.timeout and now - start_time > self.timeout:
            unfinished_msg = "Unfinished jobs:" + repr(_nested_jobs(self))
            raise FlowTimeoutException("Timeout after:" + repr(now - start_time) + " seconds. " + unfinished_msg)

    def _wait_for_jobs(self):
        print
        print 'Will run:', _nested_jobs(self)
        last_report_time = start_time = time.time()

        while 1:
            done, last_report_time, _failed = self._check_jobs(start_time, last_report_time)
            if done:
                return
            time.sleep(1)

    def __exit__(self, exc_type, exc_value, traceback):
        pass


class _Controller(_Flow):
    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type:
            return None
        self._wait_for_jobs()


class _Parallel(_Flow):
    def __enter__(self):
        print "--- quing jobs for parallel run ---"
        return self

    def invoke(self, job, **params):
        job = self._get_job(job, params)
        print "Queuing job:", job, "for parallel run"

    def _check_jobs(self, start_time, last_report_time):
        failed = []
        index = 0
        for job_details in self.jobs[:]:
            finished, last_report_time, nested_failed = _check_job(job_details, self.report_interval, last_report_time)
            if nested_failed:
                failed.append(nested_failed)

            # Remove finished jobs from job list
            if finished:
                del self.jobs[index]
                continue

            index += 1

        self._check_timeout(start_time)
        if failed:
            raise FailedJobsException("Failed jobs: " + repr([(job.name, params) for job, params in failed]))

        # Are we done?
        return not self.jobs, last_report_time, None


class _Serial(_Flow):
    def __enter__(self):
        print "--- queing jobs for serial run ---"
        return self

    def invoke(self, job, **params):
        job = self._get_job(job, params)
        print "Queuing job:", job, "for serial run"

    def _check_jobs(self, start_time, last_report_time):
        finished, last_report_time, failed = _check_job(self.jobs[0], self.report_interval, last_report_time)

        # Remove finished jobs from job list
        if finished:
            del self.jobs[0]

        self._check_timeout(start_time)
        if failed:
            raise FailedJobsException("Failed job: " + repr(failed))

        # Are we done?
        return not self.jobs, last_report_time, None


class parallel(_Parallel, _Controller):
    pass


class serial(_Serial, _Controller):
    pass
