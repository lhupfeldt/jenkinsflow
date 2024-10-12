# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from datetime import datetime

import pytest

from jenkinsflow.flow import serial
from jenkinsflow.jenkins_api import Jenkins


from .framework.cfg import jenkins_security as security, ApiType


@pytest.mark.apis(ApiType.JENKINS)
def test_gh_folder_build_branch(api_type):
    url = "http://localhost:8080"
    api = Jenkins(url, username=security.username, password=security.password) if security.default_use_login else Jenkins(url)
    with serial(api, timeout=20, report_interval=1) as ctrl1:
        ctrl1.invoke("gh-org/jenkinsflow-gh-folder-test/main")


@pytest.mark.apis(ApiType.JENKINS)
def test_gh_folder_build_slow_branch(api_type):
    url = "http://localhost:8080"
    api = Jenkins(url, username=security.username, password=security.password) if security.default_use_login else Jenkins(url)
    before = datetime.now()

    with serial(api, timeout=70, report_interval=1) as ctrl1:
        ctrl1.invoke("gh-org/jenkinsflow-gh-folder-test/slow")

    # The job sleeps 10s
    assert (datetime.now() - before).total_seconds() >= 10


@pytest.mark.apis(ApiType.JENKINS)
def test_gh_folder_scan_organization(api_type):
    url = "http://localhost:8080"
    api = Jenkins(url, username=security.username, password=security.password) if security.default_use_login else Jenkins(url)
    with serial(api, timeout=20, report_interval=1) as ctrl1:
        ctrl1.invoke("gh-org")


@pytest.mark.apis(ApiType.JENKINS)
def test_gh_folder_scan_repo(api_type):
    url = "http://localhost:8080"
    api = Jenkins(url, username=security.username, password=security.password) if security.default_use_login else Jenkins(url)
    with serial(api, timeout=20, report_interval=1) as ctrl1:
        ctrl1.invoke("gh-org/jenkinsflow-gh-folder-test")
