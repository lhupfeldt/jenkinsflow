# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import os, sys, re, subprocess32
from os.path import join as jp
from pytest import raises

from jenkinsflow.flow import parallel, FailedChildJobsException

from .framework import api_select
from .framework.utils import assert_lines_in

from .cfg import ApiType

here = os.path.abspath(os.path.dirname(__file__))


def test_abort(capsys):
    with api_select.api(__file__, login=True) as api:
        if api.api_type == ApiType.SCRIPT:
            return

        api.flow_job()
        api.job('quick', exec_time=0.01, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('wait10_abort', exec_time=10, max_fails=0, expect_invocations=1, expect_order=1, final_result='ABORTED')
        api.job('wait1_fail', exec_time=1, max_fails=1, expect_invocations=1, expect_order=1)
        
        if api.api_type != ApiType.MOCK:
            subprocess32.Popen([sys.executable, jp(here, "abort_job.py"), __file__, 'abort', 'wait10_abort'])
        
        with raises(FailedChildJobsException) as exinfo:
            with parallel(api, timeout=40, job_name_prefix=api.job_name_prefix, report_interval=3) as ctrl:
                ctrl.invoke('quick')
                ctrl.invoke('wait10_abort')
                ctrl.invoke('wait1_fail')

        assert "wait10_abort" in exinfo.value.message
        assert "wait1_fail" in exinfo.value.message

        sout, _ = capsys.readouterr()
        assert_lines_in(
            sout,
            re.compile("^ABORTED: 'jenkinsflow_test__abort__wait10_abort' - build: .*/jenkinsflow_test__abort__wait10_abort.* after:"),
        )
