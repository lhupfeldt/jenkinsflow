# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from pytest import raises

from jenkinsflow import jenkins_api


def test_jenkins_api_init_api_no_password(api_type):
    with raises(Exception) as exinfo:
        jenkins_api.Jenkins("dummy", "dummy", username="hugo")
    assert "You must specify both username and password or neither" in str(exinfo.value)
