#!/usr/bin/python

import time

def _wait_for_jobs(jobs, old_builds, timeout=None, report_interval=5):
    print 'Waiting for jobs:', repr(jobs)
    last_report_time = start_time = now = time.time()

    new_builds = {}
    while len(new_builds) < len(old_builds):
        for job in jobs:
            build = job.get_last_build()
            print "Job:", job, " status - running:", job.is_running(), ", queued:", job.is_queued(), "- latest build: ", build
            if build.buildno != old_builds[job.name].buildno:
                assert build.buildno == old_builds[job.name].buildno + 1, "Oops buildno jumped!"
                # TODO: just get old_no + 1?
                new_builds[job.name] = build
        time.sleep(1)


    finished_builds = {}
    failed = []

    while len(finished_builds) < len(old_builds):
        for job in jobs:
            build = new_builds[job.name]
            
            is_running = build.is_running()
            if is_running:
                if now - last_report_time >= report_interval:
                    print "Job:", job, " status - running:", is_running, "- latest build: ", build
                    last_report_time = now
                continue

            if not finished_builds.get(job.name):
                status = build.get_status()
                if status != 'SUCCESS':
                    failed.append(job)
                print status, ":", repr(job.name), "- build: ", build.get_result_url()
                finished_builds[job.name] = build

        time.sleep(1)

        now = time.time()
        elapsed_since_start = now - start_time
        if timeout and elapsed_since_start > timeout:
            raise Exception("Timeout after:" + repr(elapsed_since_start) + " seconds")

    if failed:
        raise Exception("Failed builds: " + repr(failed))

class _flow(object):
    def __init__(self, jenkins_api, timeout, report_interval=5):
        self.api = jenkins_api
        self.timeout = timeout
        self.report_interval = report_interval
        self.jobs = []
        self.old_builds = {}

    def invoke(self, job):
        if isinstance(job, str):
            job = self.api.get_job(job)
        self.jobs.append(job)

        build = job.get_last_build()
        self.old_builds[job.name] = build
        print "Job:", repr(job.name), " status - running:", job.is_running(), ", queued:", job.is_queued(), "- latest build: ", build
        return job

    def __enter__(self):
        return self


class parallel(_flow):
    def invoke(self, job):
        job = super(parallel, self).invoke(job)
        print "Invoking job:", job
        job.invoke(invoke_pre_check_delay=0, block=False)

    def __enter__(self):
        print ""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        print "Invoked all"
        if exc_type:
            return None
        _wait_for_jobs(self.jobs, self.old_builds, self.timeout)
        print ""


class serial(_flow):
    def invoke(self, job):
        job = super(serial, self).invoke(job)
        print "Queuing job:", job

    def __enter__(self):
        print ""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type:
            return None
        for job in self.jobs:
            print "Invoking job:", job
            job.invoke(invoke_pre_check_delay=0, block=False)
            _wait_for_jobs([job], {job.name:self.old_builds[job.name]}, self.timeout)
        print ""
