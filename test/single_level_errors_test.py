# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import re
from pytest import raises

from jenkinsflow.flow import parallel, serial, FailedChildJobException, FailedChildJobsException
from .framework import api_select
from .framework.utils import assert_lines_in


def test_single_level_errors_parallel(capsys):
    with api_select.api(__file__) as api:
        api.flow_job()
        api.job('quick', exec_time=0.01, max_fails=0, expect_invocations=1, expect_order=1, params=(('s1', '', 'desc'), ('c1', 'false', 'desc')))
        api.job('quick_fail', exec_time=0.01, max_fails=1, expect_invocations=1, expect_order=1)
        api.job('wait10', exec_time=10, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('wait10_fail', exec_time=10, max_fails=1, expect_invocations=1, expect_order=1)
        api.job('wait5', exec_time=5, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('wait5_fail', exec_time=5, max_fails=1, expect_invocations=1, expect_order=1)

        with raises(FailedChildJobsException) as exinfo:
            with parallel(api, timeout=40, job_name_prefix=api.job_name_prefix, report_interval=3) as ctrl:
                ctrl.invoke('quick', s1='', c1=False)
                ctrl.invoke('quick_fail')
                ctrl.invoke('wait10')
                ctrl.invoke('wait10_fail')
                ctrl.invoke('wait5')
                ctrl.invoke('wait5_fail')

        assert "quick_fail" in exinfo.value.message
        assert "wait10_fail" in exinfo.value.message
        assert "wait5_fail" in exinfo.value.message

        sout, _ = capsys.readouterr()
        assert_lines_in(
            sout,
            re.compile("^FAILURE: 'jenkinsflow_test__single_level_errors_parallel__quick_fail' - build: .*/jenkinsflow_test__single_level_errors_parallel__quick_fail.* after:"),
        )


def test_single_level_errors_serial():
    with api_select.api(__file__) as api:
        api.job('quick', exec_time=0.01, max_fails=0, expect_invocations=1, expect_order=1, params=(('s1', '', 'desc'), ('c1', 'false', 'desc')))
        api.job('quick_fail', exec_time=0.01, max_fails=1, expect_invocations=1, expect_order=2, serial=True)
        api.job('wait5', exec_time=5, max_fails=0, expect_invocations=0, expect_order=None)

        with raises(FailedChildJobException):
            with serial(api, timeout=20, job_name_prefix=api.job_name_prefix, report_interval=3) as ctrl:
                ctrl.invoke('quick', s1='', c1=False)
                ctrl.invoke('quick_fail')
                ctrl.invoke('wait5')
