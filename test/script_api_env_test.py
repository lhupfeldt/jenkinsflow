# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import os

import pytest

from jenkinsflow.flow import serial

from .framework import api_select
from .cfg import ApiType


@pytest.mark.apis(ApiType.SCRIPT)
def test_script_api_env_unchanged(api_type):
    """Ensure that os.environ is unchanged after run of slow using script_api"""

    env_before = os.environ.copy()

    with api_select.api(__file__, api_type, login=True) as api:
        api.flow_job()
        job_name = 'job-1'
        api.job(job_name, max_fails=0, expect_invocations=1, expect_order=1)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=1) as ctrl1:
            ctrl1.invoke(job_name)

        # Do a few more things to 
        job = api.get_job(api.job_name_prefix + job_name)
        _, _, build_num = job.job_status()

    assert os.environ == env_before
