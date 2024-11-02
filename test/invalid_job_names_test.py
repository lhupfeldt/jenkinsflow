# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import pytest

from jenkinsflow.flow import serial
from jenkinsflow.jenkins_api import JenkinsApi
from jenkinsflow.api_base import InvalidJobNameException


from .framework.cfg import ApiType


@pytest.mark.apis(ApiType.JENKINS)
def test_invalid_job_in_gh_folder_name(api_type):
    url = "http://localhost:8080"
    api = JenkinsApi(url)
    with pytest.raises(InvalidJobNameException):
        with serial(api, timeout=20, report_interval=1) as ctrl1:
            ctrl1.invoke("gh-org/job/jenkinsflow-gh-folder-test/job/main")
