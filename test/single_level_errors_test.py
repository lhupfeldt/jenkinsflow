# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import re
from pytest import raises

from jenkinsflow.flow import parallel, serial, FailedChildJobException, FailedChildJobsException
from .framework import api_select
from .framework.utils import lines_in


def test_single_level_errors_parallel(api_type, capsys):
    with api_select.api(__file__, api_type) as api:
        api.flow_job()
        api.job('quick', max_fails=0, expect_invocations=1, expect_order=1, params=(('s1', '', 'desc'), ('c1', 'false', 'desc')))
        api.job('quick_fail', max_fails=1, expect_invocations=1, expect_order=1)
        api.job('wait10', max_fails=0, expect_invocations=1, expect_order=1, exec_time=10)
        api.job('wait10_fail', max_fails=1, expect_invocations=1, expect_order=1, exec_time=10)
        api.job('wait5', max_fails=0, expect_invocations=1, expect_order=1, exec_time=5)
        api.job('wait5_fail', max_fails=1, expect_invocations=1, expect_order=1, exec_time=5)

        with raises(FailedChildJobsException) as exinfo:
            with parallel(api, timeout=40, job_name_prefix=api.job_name_prefix, report_interval=3) as ctrl:
                ctrl.invoke('quick', s1='', c1=False)
                ctrl.invoke('quick_fail')
                ctrl.invoke('wait10')
                ctrl.invoke('wait10_fail')
                ctrl.invoke('wait5')
                ctrl.invoke('wait5_fail')

        assert "quick_fail" in str(exinfo.value)
        assert "wait10_fail" in str(exinfo.value)
        assert "wait5_fail" in str(exinfo.value)

        sout, _ = capsys.readouterr()
        assert lines_in(
            api_type, sout,
            re.compile("^FAILURE: 'jenkinsflow_test__single_level_errors_parallel__quick_fail' - build: .*/jenkinsflow_test__single_level_errors_parallel__quick_fail.* after:"),
        )


def test_single_level_errors_serial(api_type):
    with api_select.api(__file__, api_type) as api:
        api.job('quick', max_fails=0, expect_invocations=1, expect_order=1, params=(('s1', '', 'desc'), ('c1', 'false', 'desc')))
        api.job('quick_fail', max_fails=1, expect_invocations=1, expect_order=2, serial=True)
        api.job('wait5', max_fails=0, expect_invocations=0, expect_order=None, exec_time=5)

        with raises(FailedChildJobException):
            with serial(api, timeout=20, job_name_prefix=api.job_name_prefix, report_interval=3) as ctrl:
                ctrl.invoke('quick', s1='', c1=False)
                ctrl.invoke('quick_fail')
                ctrl.invoke('wait5')
