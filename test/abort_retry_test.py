# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import sys, os, subprocess32
from os.path import join as jp

from pytest import raises, fail

from jenkinsflow.flow import parallel, serial, FailedChildJobException, FailedChildJobsException

from .framework import api_select
from .cfg import ApiType

here = os.path.abspath(os.path.dirname(__file__))


def test_abort_retry_serial_toplevel():
    with api_select.api(__file__) as api:
        if api.api_type == ApiType.SCRIPT:
            return

        api.flow_job()
        api.job('j11', 0.01, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j12_abort', 10, max_fails=0, expect_invocations=1, expect_order=2, serial=True, final_result='ABORTED')
        api.job('j13', 0.01, max_fails=0, expect_invocations=0, expect_order=None, serial=True)

        if api.api_type != ApiType.MOCK:
            subprocess32.Popen([sys.executable, jp(here, "abort_job.py"), __file__, 'abort_retry_serial_toplevel', 'j12_abort'])

        with raises(FailedChildJobException):
            with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, max_tries=2) as ctrl1:
                ctrl1.invoke('j11')
                ctrl1.invoke('j12_abort')
                ctrl1.invoke('j13')


def test_abort_retry_parallel_toplevel():
    with api_select.api(__file__) as api:
        if api.api_type == ApiType.SCRIPT:
            return

        api.flow_job()
        api.job('j11', 0.01, max_fails=0, expect_invocations=1, expect_order=None)
        api.job('j12_abort', 10, max_fails=0, expect_invocations=1, expect_order=None, final_result='ABORTED')
        api.job('j13', 0.01, max_fails=0, expect_invocations=1, expect_order=None)

        if api.api_type != ApiType.MOCK:
            subprocess32.Popen([sys.executable, jp(here, "abort_job.py"), __file__, 'abort_retry_parallel_toplevel', 'j12_abort'])

        with raises(FailedChildJobsException):
            with parallel(api, timeout=70, job_name_prefix=api.job_name_prefix, max_tries=2) as ctrl1:
                ctrl1.invoke('j11')
                ctrl1.invoke('j12_abort')
                ctrl1.invoke('j13')


