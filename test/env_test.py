# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from jenkinsflow.flow import serial
from .cfg import ApiType
from .framework import api_select


def test_env_variables():
    with api_select.api(__file__) as api:
        if api.api_type != ApiType.SCRIPT:
            return
        
        api.flow_job()
        api.job('j11', 0.1, max_fails=0, expect_invocations=1, expect_order=1, print_env=True)
        api.job('j12', 1.5, max_fails=0, expect_invocations=1, invocation_delay=1.0, initial_buildno=7, expect_order=2, serial=True, print_env=True)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix) as ctrl1:
            ctrl1.invoke('j11')
            ctrl1.invoke('j12')

        # TODO, check for env variables in log files
