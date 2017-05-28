# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from jenkinsflow.flow import serial
from .framework import api_select

# TODO: Actually test that cause is set

def test_cause_no_build_number(api_type, env_job_name):
    with api_select.api(__file__, api_type) as api:
        api.flow_job()
        api.job('j1', max_fails=0, expect_invocations=1, expect_order=1)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=1) as ctrl1:
            ctrl1.invoke('j1')


def test_cause(api_type, env_job_name, env_build_number):
    with api_select.api(__file__, api_type) as api:
        api.flow_job()
        api.job('j1', max_fails=0, expect_invocations=1, expect_order=1)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=1) as ctrl1:
            ctrl1.invoke('j1')


