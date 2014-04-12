# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import jenkinsapi
from peak.util.proxies import ObjectWrapper
from .specialized_api import UnknownJobException


class Jenkins(jenkinsapi.jenkins.Jenkins):
    job_prefix_filter = direct_uri = None

    def __init__(self, direct_uri, job_prefix_filter=None, username=None, password=None):
        super(Jenkins, self).__init__(direct_uri, username=username, password=password)
        self.job_prefix_filter = job_prefix_filter
        self.direct_uri = direct_uri

    def get_job(self, name):
        try:
            jenkins_job = super(Jenkins, self).get_job(name)
        except jenkinsapi.custom_exceptions.UnknownJob as ex:
            raise UnknownJobException(str(ex))
        return ApiJob(jenkins_job)

    def delete_job(self, name):
        try:
            return super(Jenkins, self).delete_job(name)
        except jenkinsapi.custom_exceptions.UnknownJob as ex:
            raise UnknownJobException(str(ex))

    def quick_poll(self):
        pass


class ApiJob(ObjectWrapper, jenkinsapi.job.Job):
    non_clickable_build_trigger_url = None

    def __init__(self, jenkins_job):
        ObjectWrapper.__init__(self, jenkins_job)
        params = jenkins_job.get_params_list()
        self.non_clickable_build_trigger_url = self.baseurl if not params else self.baseurl + " - parameters:"

    def invoke(self, securitytoken, build_params, cause):
        self.__subject__.invoke(securitytoken=securitytoken, invoke_pre_check_delay=0, block=False, build_params=build_params, cause=cause)

    def get_last_build_or_none(self):
        for ii in range(1, 20):
            try:
                self.__subject__.poll()
                build = self.__subject__.get_last_build_or_none()
                return ApiBuild(build, self) if build is not None else build
            except KeyError as ex:  # pragma: no cover
                # Workaround for jenkinsapi timing dependency?
                if ii == 1:
                    print("poll or get_last_build_or_none' failed: " + str(ex) + ", retrying.")
                    traceback.print_exc()
                hyperspeed.sleep(0.1)


class ApiBuild(ObjectWrapper, jenkinsapi.build.Build):
    job = None

    def __init__(self, jenkins_build, job):
        ObjectWrapper.__init__(self, jenkins_build)
        self.job = job

    def console_url(self):
        return self.job.baseurl + '/' + str(self.buildno) + '/console'

    def __repr__(self):
        return self.job.name + " #" + repr(self.buildno)
