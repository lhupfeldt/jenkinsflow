# Copyright (c) 2017 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import pytest

from jenkinsflow.flow import serial, FailedChildJobException, FailedChildJobsException

from .framework import api_select
from .cfg import ApiType


def _job_name(api, short_name):
    return api.job_name_prefix + short_name, short_name


@pytest.mark.not_apis(ApiType.MOCK, ApiType.SCRIPT)
def test_enable_disable_disable_enable(api_type):
    with api_select.api(__file__, api_type, login=True) as api:
        full_name, short_name = _job_name(api, 'j1')
        api.job(short_name, max_fails=0, expect_invocations=0, expect_order=None)

        api.poll()
        job = api.get_job(full_name)
        job.disable()
        job.enable()


@pytest.mark.not_apis(ApiType.MOCK, ApiType.SCRIPT)
def test_enable_disable_invoke_disabled(api_type):
    with api_select.api(__file__, api_type, login=True) as api:
        full_name, short_name = _job_name(api, 'j1_disabled_invoke')
        api.job(short_name, max_fails=1, expect_invocations=0, expect_order=None)

        api.poll()
        job = api.get_job(full_name)
        job.disable()

        with pytest.raises(Exception):  # TODO improved error handlng when invoking disabled jobs
            with serial(api, timeout=50, job_name_prefix=api.job_name_prefix, report_interval=1) as ctrl1:
                ctrl1.invoke('j1_disabled_invoke')

        job.enable()
