# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import jenkinsapi
from .specialized_api import UnknownJobException


class Jenkins(jenkinsapi.jenkins.Jenkins):
    def __init__(self, direct_uri, job_prefix_filter=None, username=None, password=None):
        super(Jenkins, self).__init__(direct_uri, username=username, password=password)

        self.job_prefix_filter = job_prefix_filter
        self.direct_uri = direct_uri

    def get_job(self, name):
        try:
            return super(Jenkins, self).get_job(name)
        except jenkinsapi.custom_exceptions.UnknownJob as ex:
            raise UnknownJobException(str(ex))

    def delete_job(self, name):
        try:
            return super(Jenkins, self).delete_job(name)
        except jenkinsapi.custom_exceptions.UnknownJob as ex:
            raise UnknownJobException(str(ex))
