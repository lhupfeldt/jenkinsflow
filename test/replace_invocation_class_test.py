# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import re
import pytest

from jenkinsflow.flow import parallel, serial, FailedChildJobException, FailedChildJobsException
from .framework import api_select
from .framework.utils import lines_in
from .cfg import ApiType


@pytest.mark.not_apis(ApiType.MOCK)
def test_replace_invocation_class_log_override(api_type, capsys):
    if api_type == ApiType.JENKINS:
        from jenkinsflow.jenkins_api import Invocation

        class LogInvocation(Invocation):
            def console_url(self):
                return "HELLO LOG"

    elif api_type == ApiType.SCRIPT:
        from jenkinsflow.script_api import Invocation

        class LogInvocation(Invocation):
            def console_url(self):
                return "HELLO LOG"
    else:
        raise Exception("Invalid ApiType: " + repr(api_type))

    with api_select.api(__file__, api_type, invocation_class=LogInvocation) as api:
        api.flow_job()
        api.job('j1', max_fails=0, expect_invocations=1, expect_order=1, params=(('s1', '', 'desc'), ('c1', 'false', 'desc')))
        api.job('j2', max_fails=0, expect_invocations=1, expect_order=1, params=(('s1', '', 'desc'), ('c1', 'false', 'desc')))

        with parallel(api, timeout=40, job_name_prefix=api.job_name_prefix, report_interval=3) as ctrl:
            ctrl.invoke('j1', s1='', c1=False)
            ctrl.invoke('j2', s1='', c1=False)

        sout, _ = capsys.readouterr()
        assert "HELLO LOG" in sout


