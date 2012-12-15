#!/usr/bin/python

import time
import abc


class FlowTimeoutException(Exception):
    pass


class FailedJobsException(Exception):
    pass


def _print_status_message(job, build):
    print "Status", repr(job.name), "- running:", repr(job.is_running()) + ", queued:", job.is_queued(), "- latest build: ", build


def _wait_for_jobs(jobs, timeout, report_interval):
    print 'Waiting for:', [job.name for job, _params, _old_build in jobs]
    last_report_time = start_time = now = time.time()

    num_builds = len(jobs)
    num_finished_builds = 0
    failed = []

    while num_finished_builds < num_builds:
        index = 0
        for job, params, old_build in jobs[:]:
            job.poll()
            build = job.get_last_build_or_none()
            if build == None:
                continue

            old_buildno = (old_build.buildno if old_build else None)
            if build.buildno == old_buildno or build.is_running():
                if now - last_report_time >= report_interval:
                    _print_status_message(job, build)
                    last_report_time = now
                continue

            _print_status_message(job, build)
            if not build.is_good():
                failed.append((job, params))
            print build.get_status(), ":", repr(job.name), "- build: ", build.get_result_url()
            del jobs[index]
            index += 1
            num_finished_builds += 1

        time.sleep(1)

        now = time.time()
        if timeout and now - start_time > timeout:
            raise FlowTimeoutException("Timeout after:" + repr(now - start_time) + " seconds. Unfinished jobs:"
                                       + repr([(job.name, params) for job, params, _builds in jobs]))

    if failed:
        raise FailedJobsException("Failed builds: " + repr([(job.name, params) for job, params in failed]))


class _Flow(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, jenkins_api, timeout, report_interval=5):
        self.api = jenkins_api
        self.timeout = timeout
        self.report_interval = report_interval
        self.jobs = []

    @abc.abstractmethod
    def invoke(self, job, **params):
        if isinstance(job, str):
            job = self.api.get_job(job)
        old_build = job.get_last_build_or_none()
        self.jobs.append((job, params, old_build))
        _print_status_message(job, old_build)
        return job


class parallel(_Flow):
    def invoke(self, job, **params):
        job = super(parallel, self).invoke(job, **params)
        print "Invoking:", repr(job.name)
        job.invoke(invoke_pre_check_delay=0, block=False, params=params)

    def __enter__(self):
        print "--- starting parallel run ---"
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type:
            return None
        _wait_for_jobs(self.jobs, self.timeout, self.report_interval)
        print ""


class serial(_Flow):
    def invoke(self, job, **params):
        job = super(serial, self).invoke(job, **params)
        print "Queuing job:", job

    def __enter__(self):
        print "--- starting serial run ---"
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type:
            return None
        for job, params, old_build in self.jobs:
            print "Invoking:", repr(job.name)
            job.invoke(invoke_pre_check_delay=0, block=False, params=params)
            _wait_for_jobs([(job, params, old_build)], self.timeout, self.report_interval)
        print ""
