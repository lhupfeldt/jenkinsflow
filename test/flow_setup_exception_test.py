# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from pytest import raises

from jenkinsflow.flow import parallel, serial
from .framework import api_select


def test_flow_setup_exception_job(api_type):
    with api_select.api(__file__, api_type) as api:
        api.flow_job()
        api.job('j1', max_fails=0, expect_invocations=0, expect_order=None)

        with raises(Exception) as exinfo:
            with serial(api, 10, job_name_prefix=api.job_name_prefix) as ctrl1:
                raise Exception("Not good")
            ctrl1.invoke('j1')

        assert str(exinfo.value) == "Not good"

        with raises(Exception) as exinfo:
            with parallel(api, 10, job_name_prefix=api.job_name_prefix) as ctrl1:
                raise Exception("Not good")
            ctrl1.invoke('j1')

        assert str(exinfo.value) == "Not good"
