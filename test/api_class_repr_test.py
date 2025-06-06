# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import pytest

from jenkinsflow import jenkins_api

from .framework import api_select
from .framework.cfg import ApiType


@pytest.mark.not_apis(ApiType.MOCK, ApiType.SCRIPT)
def test_api_class_repr_job(api_type):
    api = api_select.api(__file__, api_type, login=True)
    job = jenkins_api.ApiJob(api, {}, 'my-job', has_children=False)

    jrd = eval(repr(job))
    assert jrd == {'name': 'my-job', 'dct': {}}

    invocation = jenkins_api.Invocation(job, "http://dummy", 'hello')
    assert repr(invocation) == "Invocation: 'http://dummy' None None"
