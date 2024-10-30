# Copyright (c) 2012 - 2024 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import os
from enum import Enum
import urllib.parse

from .ordered_enum import OrderedEnum


class BuildResult(OrderedEnum):
    FAILURE = 0
    ABORTED = 1
    UNSTABLE = 2
    SUCCESS = 3
    SUPERSEDED = 4
    DEQUEUED = 5
    UNKNOWN = 6


class Progress(Enum):
    RUNNING = 1
    QUEUED = 2
    IDLE = 3


class AuthError(Exception):
    pass


class ClientError(AuthError):
    pass


class UnknownJobException(Exception):
    def __init__(self, job_url, api_ex=None):
        super().__init__("Job not found: " + job_url + (", " + repr(api_ex) if api_ex is not None else ""))


class InvalidJobNameException(Exception):
    def __init__(self, job_name):
        super().__init__(f"Invalid job name '{job_name}'. Job name should be either '<name>' or '<github-organization>[/<repo>[/<branch>]]'.")


class BaseApiMixin():
    def get_build_url(self, build_url: str = None, job_name: str = None, build_number: int = None):
        """Get the build_url either from arguments or environment.

        Arguments are preferred if specified and 'build_url' is preferred over job_name and build_number.
        """

        if build_url is None and job_name is None and build_number is None:
            try:
                build_url = os.environ['BUILD_URL']
            except KeyError:
                pass

        if build_url is not None:
            # Make build_url relative
            build_url = urllib.parse.urlsplit(build_url).path
            if self.jenkins_prefix:
                return os.path.relpath(build_url, self.jenkins_prefix)
            return build_url

        job_name = job_name if job_name is not None else os.environ['JOB_NAME']
        build_number = build_number if build_number is not None else int(os.environ['BUILD_NUMBER'])
        return f"/job/{job_name}/{build_number}"

    @staticmethod
    def get_name_for_query(job_name_prefix: str, job_name: str) -> str:
        job_name = job_name.strip("/")
        parts = job_name.split("/")

        if len(parts) == 1:
            return job_name_prefix + job_name

        if len(parts) == 2:
            return parts[0] + "/job/" + job_name_prefix + parts[1]

        if len(parts) == 3:
            return parts[0] + "/job/" + job_name_prefix + parts[1] +  "/job/" + parts[2]

        raise InvalidJobNameException(job_name)


class ApiInvocationMixin():
    def console_url(self):
        return (self.job.public_uri + '/' + repr(self.build_number) + '/console') if self.build_number is not None else None
