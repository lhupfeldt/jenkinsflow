# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from enum import Enum
from .ordered_enum import OrderedEnum


class BuildResult(OrderedEnum):
    # pylint: disable=no-init
    FAILURE = 0
    ABORTED = 1
    UNSTABLE = 2
    SUCCESS = 3
    SUPERSEDED = 4
    DEQUEUED = 5
    UNKNOWN = 6


class Progress(Enum):
    # pylint: disable=no-init
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


class ApiInvocationMixin():
    def console_url(self):
        return (self.job.public_uri + '/' + repr(self.build_number) + '/console') if self.build_number is not None else None
