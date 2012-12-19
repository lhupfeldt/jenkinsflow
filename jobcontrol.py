# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import time
import abc

_default_report_interval = 5

def _print_status_message(jenkins_job, build):
    print "Status", repr(jenkins_job.name), "- running:", repr(jenkins_job.is_running()) + ", queued:", jenkins_job.is_queued(), "- latest build: ", build


class FlowTimeoutException(Exception):
    pass


class FailedJobsException(Exception):
    pass


class _JobControl(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, report_interval):
        self.report_interval = report_interval
        self.invoked = 0
        self.finished = False
        self.successful = False

    @abc.abstractmethod
    def _check(self, start_time, last_report_time):
        pass

    @abc.abstractmethod
    def sequence(self):
        pass

    def __repr__(self):
        return str(self.sequence())


class _SingleJob(_JobControl):
    def __init__(self, jenkins_api, job_name_prefix, job_name, params, report_interval):
        super(_SingleJob, self).__init__(report_interval)

        job = jenkins_api.get_job(job_name_prefix + job_name)
        self.old_build = job.get_last_build_or_none()
        _print_status_message(job, self.old_build)

        self.job = job
        self.params = params

    def _check(self, start_time, last_report_time):
        if not self.invoked:
            print "Invoking:", repr(self.job.name)
            self.invoked = time.time()
            self.job.invoke(invoke_pre_check_delay=0, block=False, params=self.params)
    
        self.job.poll()
        build = self.job.get_last_build_or_none()
        if build == None:
            return last_report_time, None
    
        old_buildno = (self.old_build.buildno if self.old_build else None)
        if build.buildno == old_buildno or build.is_running():
            now = time.time()
            if now - last_report_time >= self.report_interval:
                _print_status_message(self.job, build)
                last_report_time = now
            return last_report_time, None
    
        # The job has stopped running
        self.finished = True
        self.successful = build.is_good()
        _print_status_message(self.job, build)
        print build.get_status(), ":", repr(self.job.name), "- build: ", build.get_result_url()
    
        return last_report_time, None if self.successful else (self.job, self.params)

    def sequence(self):
        return self.job.name


class _Flow(_JobControl):
    __metaclass__ = abc.ABCMeta

    def __init__(self, jenkins_api, timeout, job_name_prefix='', retries=0, report_interval=_default_report_interval):
        super(_Flow, self).__init__(report_interval)

        self.api = jenkins_api
        self.timeout = timeout
        self.job_name_prefix = job_name_prefix
        self.retries = retries
        self.report_interval = report_interval
        self.jobs = []

    def parallel(self, timeout, job_name_prefix='', retries=0, report_interval=_default_report_interval):
        pll = _Parallel(self.api, timeout, job_name_prefix=self.job_name_prefix+job_name_prefix, retries=retries, report_interval=report_interval)
        self.jobs.append(pll)
        return pll

    def serial(self, timeout, job_name_prefix='', retries=0, report_interval=_default_report_interval):
        ser = _Serial(self.api, timeout, job_name_prefix=self.job_name_prefix+job_name_prefix, retries=retries, report_interval=report_interval)
        self.jobs.append(ser)
        return ser

    def _check_timeout(self, start_time):
        if self.finished:
            return

        now = time.time()
        if self.timeout and now - start_time > self.timeout:
            unfinished_msg = "Unfinished jobs:" + str(self)
            raise FlowTimeoutException("Timeout after:" + repr(now - start_time) + " seconds. " + unfinished_msg)

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type:
            return None


class _TopLevelController(_Flow):
    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type:
            return None

        # Wait for jobs to finish
        print
        print 'Will run:', self
        last_report_time = start_time = time.time()

        while not self.finished:
            last_report_time, _failed = self._check(start_time, last_report_time)
            time.sleep(0.2)


class _Parallel(_Flow):
    def __enter__(self):
        print "--- quing jobs for parallel run ---"
        return self

    def invoke(self, job_name, **params):
        job = _SingleJob(self.api, self.job_name_prefix, job_name, params, self.report_interval)
        self.jobs.append(job)
        print "Queuing job:", job.job, "for parallel run"

    def _check(self, start_time, last_report_time):
        failed_children = []
        all_finished = True
        for job in self.jobs:
            if job.finished:
                continue
            
            all_finished = False
            last_report_time, failed_child = job._check(start_time, last_report_time)
            if failed_child:
                failed_children.append(failed_child)

        self._check_timeout(start_time)
        if failed_children:
            raise FailedJobsException("Failed jobs: " + repr([(job.name, params) for job, params in failed_children]))

        self.finished = all_finished
        return last_report_time, None

    def sequence(self):
        return tuple([job.sequence() for job in self.jobs])


class _Serial(_Flow):
    def __init__(self, jenkins_api, timeout, job_name_prefix='', retries=0, report_interval=_default_report_interval):
        super(_Serial, self).__init__(jenkins_api, timeout, job_name_prefix, retries, report_interval)
        self.next_index = 0

    def __enter__(self):
        print "--- queing jobs for serial run ---"
        return self

    def invoke(self, job_name, **params):
        job = _SingleJob(self.api, self.job_name_prefix, job_name, params, self.report_interval)
        self.jobs.append(job)
        print "Queuing job:", job.job, "for serial run"

    def _check(self, start_time, last_report_time):
        if self.jobs[self.next_index].finished:
            self.next_index += 1
            if self.next_index == len(self.jobs):
                self.finished = True
            return last_report_time, None

        last_report_time, failed_child = self.jobs[self.next_index]._check(start_time, last_report_time)

        self._check_timeout(start_time)
        if failed_child:
            raise FailedJobsException("Failed job: " + repr(failed_child))

        return last_report_time, None

    def sequence(self):
        return [job.sequence() for job in self.jobs]


class parallel(_Parallel, _TopLevelController):
    pass


class serial(_Serial, _TopLevelController):
    pass
