# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import pytest

from jenkinsflow import flow
from jenkinsflow.api_base import AuthError


import demo_security as security

from .framework import api_select
from .cfg import ApiType


@pytest.mark.not_apis(ApiType.MOCK, ApiType.SCRIPT)
def test_unicode_auth_latin1(api_type):
    with api_select.api(__file__, api_type, username="jenkinsflow_authtest1", password=r'abcæøåÆØÅ') as api:
        api.flow_job()
        api.job('j11', max_fails=0, expect_invocations=1, invocation_delay=1.0, expect_order=1)

        with flow.serial(api, timeout=70, job_name_prefix=api.job_name_prefix) as ctrl1:
            ctrl1.invoke('j11')


@pytest.mark.not_apis(ApiType.MOCK, ApiType.SCRIPT)
def test_unicode_auth_utf8(api_type):
    pytest.xfail("BasicAuth does not support unicode")  # TODO, if that gets supported, then enable this
    with api_select.api(__file__, api_type, username="jenkinsflow_authtest2", password=u'æøå¶¹²³³¼¢⅝÷«') as api:
        api.flow_job()
        api.job('j11', max_fails=0, expect_invocations=1, invocation_delay=1.0, expect_order=1)

        with flow.serial(api, timeout=70, job_name_prefix=api.job_name_prefix) as ctrl1:
            ctrl1.invoke('j11')


@pytest.mark.not_apis(ApiType.MOCK, ApiType.SCRIPT)
def test_unicode_auth_ascii(api_type):
    """Ensure that login without unicode works"""

    with api_select.api(__file__, api_type, username=security.username, password=security.password) as api:
        api.flow_job()
        api.job('j11', max_fails=0, expect_invocations=1, invocation_delay=1.0, expect_order=1)

        with flow.serial(api, timeout=70, job_name_prefix=api.job_name_prefix) as ctrl1:
            ctrl1.invoke('j11')


@pytest.mark.not_apis(ApiType.MOCK, ApiType.SCRIPT)
def test_unicode_auth_failed_login(api_type):
    """Ensure that login with bad password fails in a reasonable way."""

    with pytest.raises(AuthError) as exinfo:
        with api_select.api(__file__, api_type, username=security.username, password='notright') as api:
            api.flow_job()

    assert ("401 Client Error: Invalid password/token for user: jenkinsflow_jobrunner" in str(exinfo.value) or
            "401 Unauthorized user: 'jenkinsflow_jobrunner' for url: http://")
