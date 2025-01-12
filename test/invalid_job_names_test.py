# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import pytest

from jenkinsflow.flow import serial
from jenkinsflow.jenkins_api import JenkinsApi
from jenkinsflow.api_base import InvalidJobNameException


from .framework.cfg import ApiType


@pytest.mark.apis(ApiType.JENKINS)
@pytest.mark.parametrize("org_name", ["codeberg-org-jenkinsflow-test", "github-org-jenkinsflow-test"])
def test_invalid_job_in_org_folder_name(api_type, org_name):
    url = "http://localhost:8080"
    api = JenkinsApi(url)
    with pytest.raises(InvalidJobNameException):
        with serial(api, timeout=20, report_interval=1) as ctrl1:
            # Name must not contain '/job/'
            ctrl1.invoke(f"{org_name}/job/jenkinsflow-gh-folder-test/job/main")
