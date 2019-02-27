# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from jenkinsflow.flow import serial
from .cfg import ApiType
from .framework import api_select
from .framework.utils import lines_in, build_started_msg, build_queued_msg


def test_reporting_queued(api_type, capsys):
    # TODO
    skip_apis = (ApiType.SCRIPT, ApiType.MOCK)

    with api_select.api(__file__, api_type, login=True) as api:
        api.flow_job()
        exp_invocations = 2 if api.api_type not in skip_apis else 1
        unknown_result = False if api.api_type not in skip_apis else True
        api.job('j1', max_fails=0, expect_invocations=exp_invocations, expect_order=None, exec_time=10, unknown_result=unknown_result)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix) as ctrl1:
            ctrl1.invoke_unchecked('j1')

        print(api.api_type, type(api.api_type))
        if api.api_type in skip_apis:
            return

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, require_idle=False) as ctrl1:
            ctrl1.invoke('j1')

        sout, _ = capsys.readouterr()
        assert lines_in(
            api_type, sout,
            "^Job Invocation (1/1,1/1): http://x.x/job/jenkinsflow_test__reporting_queued__j1",
            build_queued_msg(api, "jenkinsflow_test__reporting_queued__j1", 1),
            build_started_msg(api, "jenkinsflow_test__reporting_queued__j1", 2),
        )
