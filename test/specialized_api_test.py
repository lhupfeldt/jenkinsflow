# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import os
from os.path import join as jp

from pytest import raises

from jenkinsflow import specialized_api


here = os.path.abspath(os.path.dirname(__file__))

def test_specialized_api_build_repr():
    class Job(object):
        name = "Hello"
    b = specialized_api.ApiBuild(Job(), dict(number=7))
    assert repr(b) == 'Hello #7'


def test_specialized_api_init_api_no_password():
    with raises(Exception) as exinfo:
        specialized_api.Jenkins("dummy", "dummy", username="hugo")
    assert "You must specify both username and password or neither" in exinfo.value.message

