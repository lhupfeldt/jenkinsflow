# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# Abstract base classes representing the API's used from jenkins_apixk

# These classes serve as base classes for the Mock and Wrappper test API's

import abc


class AbstractApiJob(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def invoke(self, securitytoken, build_params, cause, description):
        raise Exception("AbstractNotImplemented")

    # The following should be declare abstract, but since they are 'implemented' by proxy we can't do that (conveniently)
    # def is_running(self):
    # def is_queued(self):
    # def get_last_build_or_none(self):
    # def get_build_triggerurl(self):
    # def update_config(self, config_xml):
    # def poll(self):


class AbstractApiJenkins(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def create_job(self, job_name, config_xml):
        raise Exception("AbstractNotImplemented")

    @abc.abstractmethod
    def delete_job(self, job_name):
        raise Exception("AbstractNotImplemented")

    @abc.abstractmethod
    def get_job(self, name):
        raise Exception("AbstractNotImplemented")

    @abc.abstractmethod
    def poll(self):
        raise Exception("AbstractNotImplemented")
