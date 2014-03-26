# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from jenkinsflow.flow import serial
from .framework import mock_api


def test_multiple_invocations_same_flow():
    with mock_api.api(__file__) as api:
        api.flow_job()
        _params = (('password', '', 'Some password'), ('s1', '', 'Some string argument'))
        api.job('j1', exec_time=0.01, max_fails=0, expect_invocations=2, expect_order=1, params=_params)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=1) as ctrl1:
            ctrl1.invoke('j1', password='a', s1='b')
            ctrl1.invoke('j1', password='something else', s1='asdasdasdasdad')


def test_multiple_invocations_new_flow():
    with mock_api.api(__file__) as api:
        api.flow_job()
        _params = (('password', '', 'Some password'), ('s1', '', 'Some string argument'))
        api.job('j1', exec_time=0.01, max_fails=0, expect_invocations=2, expect_order=1, params=_params)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=1) as ctrl1:
            ctrl1.invoke('j1', password='a', s1='b')

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=1) as ctrl1:
            ctrl1.invoke('j1', password='something else', s1='asdasdasdasdad')
