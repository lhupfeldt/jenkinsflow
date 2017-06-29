# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import pytest

from jenkinsflow import flow
from jenkinsflow.api_base import AuthError

from .framework import api_select
from .cfg import ApiType


@pytest.mark.not_apis(ApiType.MOCK, ApiType.SCRIPT)
def test_auth_error(api_type):
    with api_select.api(__file__, api_type, username="noaccess", password='maybegranted') as api:

        with pytest.raises(AuthError) as exinfo:
            with flow.serial(api, timeout=70, job_name_prefix=api.job_name_prefix) as ctrl1:
                ctrl1.invoke('j11')

        assert ("401 Client Error: Invalid password/token for user: noaccess for url: http://" in str(exinfo.value) or
                "401 Unauthorized user: 'noaccess' for url: http://" in str(exinfo.value))
