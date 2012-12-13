#!/usr/bin/python

import time


class FlowTimeoutException(Exception):
    pass


class FailedJobsException(Exception):
    pass


def _print_status_message(job, build):
    print "Status:", repr(job.name), " - running:", job.is_running(), ", queued:", job.is_queued(), "- latest build: ", build


def _wait_for_jobs(jobs, old_builds, timeout=None, report_interval=5):
    print 'Waiting for:', [job.name for job, _params in jobs]
    last_report_time = start_time = now = time.time()

    num_builds = len(old_builds)
    num_finished_builds = 0
    failed = []

    while num_finished_builds < num_builds:
        index = 0
        for job, _params in jobs[:]:
            old_build = old_builds[job.name]
            build = job.get_last_build()
            
            if build.buildno == old_build.buildno or build.is_running():
                if now - last_report_time >= report_interval:
                    _print_status_message(job, build)
                    last_report_time = now
                continue

            _print_status_message(job, build)
            if not build.is_good():
                failed.append(job)
            print build.get_status(), ":", repr(job.name), "- build: ", build.get_result_url()            
            del jobs[index]
            index += 1
            num_finished_builds += 1

        time.sleep(1)

        now = time.time()
        if timeout and now - start_time > timeout:
            raise FlowTimeoutException("Timeout after:" + repr(now - start_time) + " seconds")

    if failed:
        raise FailedJobsException("Failed builds: " + repr([(job.name, params) for job, params in failed]))


class _flow(object):
    def __init__(self, jenkins_api, timeout, report_interval=5):
        self.api = jenkins_api
        self.timeout = timeout
        self.report_interval = report_interval
        self.jobs = []
        self.old_builds = {}

    def invoke(self, job, **params):
        if isinstance(job, str):
            job = self.api.get_job(job)
        self.jobs.append((job, params))

        build = job.get_last_build()
        self.old_builds[job.name] = build
        _print_status_message(job, build)
        return job

    def __enter__(self):
        return self


class parallel(_flow):
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
        _wait_for_jobs(self.jobs, self.old_builds, self.timeout)
        print ""


class serial(_flow):
    def invoke(self, job, **params):
        job = super(serial, self).invoke(job, **params)
        print "Queuing job:", job

    def __enter__(self):
        print "--- starting serial run ---"
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type:
            return None
        for job, params in self.jobs:
            print "Invoking:", repr(job.name)
            job.invoke(invoke_pre_check_delay=0, block=False, params=params)
            _wait_for_jobs([(job, params)], {job.name:self.old_builds[job.name]}, self.timeout)
        print ""
