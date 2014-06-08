# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

import traceback
import jenkinsapi
from peak.util.proxies import ObjectWrapper

from .api_base import UnknownJobException, ApiJobMixin, ApiBuildMixin
from .mocked import hyperspeed


class Jenkins(jenkinsapi.jenkins.Jenkins):
    """Wrapper around `jenkinsapi.jenkins.Jenkins <https://pypi.python.org/pypi/jenkinsapi>`_ which may be used for jenkinsflow to access Jenkins jobs.

    For parameters see :py:class:`.specialized_api.Jenkins`.
    """

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


class ApiJob(ObjectWrapper, jenkinsapi.job.Job, ApiJobMixin):
    non_clickable_build_trigger_url = None
    public_uri = None

    def __init__(self, jenkins_job):
        ObjectWrapper.__init__(self, jenkins_job)
        # TODO params validation? params = jenkins_job.get_params_list()
        self.public_uri = self.baseurl
        self.non_clickable_build_trigger_url = self.baseurl

    def invoke(self, securitytoken, build_params, cause):
        self.__subject__.invoke(securitytoken=securitytoken, invoke_pre_check_delay=0, block=False, build_params=build_params, cause=cause)  # pylint: disable=no-member

    def get_last_build_or_none(self):
        for ii in range(1, 20):
            try:
                self.__subject__.poll()  # pylint: disable=no-member
                build = self.__subject__.get_last_build_or_none()  # pylint: disable=no-member
                return ApiBuild(build, self) if build is not None else build
            except KeyError as ex:  # pragma: no cover
                # Workaround for jenkinsapi timing dependency?
                if ii == 1:
                    print("poll or get_last_build_or_none' failed: " + str(ex) + ", retrying.")
                    traceback.print_exc()
                hyperspeed.sleep(0.1)


class ApiBuild(ObjectWrapper, jenkinsapi.build.Build, ApiBuildMixin):
    job = None

    def __init__(self, jenkins_build, job):
        ObjectWrapper.__init__(self, jenkins_build)
        self.job = job

    def __repr__(self):
        return self.job.name + " #" + repr(self.buildno)
