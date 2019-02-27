# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import os

from pytest import xfail  # pylint: disable=no-name-in-module

from jenkinsflow.flow import serial
from jenkinsflow.rest_api_wrapper import RestkitRestApi

from .framework import api_select


_here = os.path.dirname(os.path.abspath(__file__))


def test_unicode_params_call(api_type):
    with api_select.api(__file__, api_type, login=True) as api:
        api.flow_job()
        _params = (('password', '', 'Description'),)
        api.job('job-1', max_fails=0, expect_invocations=1, expect_order=1, params=_params)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=1) as ctrl1:
            ctrl1.invoke('job-1', password='æøå˝$¼@£³¹¶⅝÷«»°¿¦')


def test_unicode_params_defaults(api_type):
    """Job load with unicode"""
    with api_select.api(__file__, api_type, login=True) as api:
        if hasattr(api, 'rest_api') and isinstance(api.rest_api, RestkitRestApi):
            xfail("TODO: this will not work with restkit.")

        api.flow_job()
        _params = (('password', 'æøå˝$¼@£³¹¶⅝÷«»°¿¦', 'Description: ÆØÅEˇé'),)
        api.job('job-1', max_fails=0, expect_invocations=1, expect_order=1, params=_params)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=1) as ctrl1:
            ctrl1.invoke('job-1', password='hello')
