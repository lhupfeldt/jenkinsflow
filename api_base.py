# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.


class UnknownJobException(Exception):
    def __init__(self, job_url):
        super(UnknownJobException, self).__init__("Job not found: " + job_url)


class ApiJobMixin(object):
    def console_url(self, buildno):
        return self.public_uri + '/' + str(buildno) + '/console'


class ApiBuildMixin(object):
    def console_url(self):
        return self.job.console_url(self.buildno)
