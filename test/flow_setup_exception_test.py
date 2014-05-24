# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from pytest import raises

from jenkinsflow.flow import parallel, serial
from .framework import api_select


def test_flow_setup_exception_job():
    with api_select.api(__file__) as api:
        api.flow_job()
        api.job('j1', 0.01, max_fails=0, expect_invocations=0, expect_order=None)

        with raises(Exception) as exinfo:
            with serial(api, 10, job_name_prefix=api.job_name_prefix) as ctrl1:
                raise Exception("Not good")
            ctrl1.invoke('j1')

        assert exinfo.value.message == "Not good"

        with raises(Exception) as exinfo:
            with parallel(api, 10, job_name_prefix=api.job_name_prefix) as ctrl1:
                raise Exception("Not good")
            ctrl1.invoke('j1')

        assert exinfo.value.message == "Not good"
