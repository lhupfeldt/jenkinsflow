# Copyright (c) 2019 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import abc

from .propagation_types import  Propagation


class JobControlException(Exception):
    def __init__(self, message, propagation=Propagation.NORMAL):
        super().__init__(message)
        self.propagation = propagation


class FlowTimeoutException(JobControlException):
    pass


class FlowScopeException(JobControlException):
    pass


class JobNotIdleException(JobControlException):
    pass


class MessageRedefinedException(JobControlException):
    pass


class JobControlFailException(JobControlException, metaclass=abc.ABCMeta):
    pass


class FailedSingleJobException(JobControlFailException):
    def __init__(self, job, propagation):
        msg = "Failed job: " + repr(job) + ", propagation:" + str(propagation)
        super().__init__(msg, propagation)


class MissingJobsException(JobControlFailException):
    def __init__(self, ex):
        super().__init__(str(ex), propagation=Propagation.NORMAL)


class FailedChildJobException(JobControlFailException):
    def __init__(self, flow_job, failed_child_job, propagation):
        msg = "Failed child job in: " + repr(flow_job) + ", child job:" + repr(failed_child_job) + ", propagation:" + str(propagation)
        super().__init__(msg, propagation)


class FailedChildJobsException(JobControlFailException):
    def __init__(self, flow_job, failed_child_jobs, propagation):
        msg = "Failed child jobs in: " + repr(flow_job) + ", child jobs:" + repr(failed_child_jobs) + ", propagation:" + str(propagation)
        super().__init__(msg, propagation)


class FinalResultException(JobControlFailException):
    def __init__(self, build_result):
        msg = "Flow Unsuccessful: {}".format(build_result)
        super().__init__(msg)
        self.result = build_result
