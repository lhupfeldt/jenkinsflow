# Copyright (c) 2024 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from datetime import datetime

import pytest

from jenkinsflow.flow import serial


from .framework.cfg import ApiType
from .framework import api_select


@pytest.mark.apis(ApiType.JENKINS)
def test_gh_folder_build_branch(api_type):
    with api_select.api(__file__, api_type, existing_jobs=True) as api:
        api.flow_job()
        api.job("gh-org/jenkinsflow-gh-folder-test/main", max_fails=0, expect_invocations=1, expect_order=1)

        with serial(api, timeout=20, report_interval=1) as ctrl1:
            ctrl1.invoke("gh-org/jenkinsflow-gh-folder-test/main")


@pytest.mark.apis(ApiType.JENKINS)
def test_gh_folder_build_slow_branch(api_type):
    with api_select.api(__file__, api_type, existing_jobs=True) as api:
        api.flow_job()
        api.job("gh-org/jenkinsflow-gh-folder-test/slow", max_fails=0, expect_invocations=1, expect_order=1)

        before = datetime.now()
        with serial(api, timeout=70, report_interval=1) as ctrl1:
            ctrl1.invoke("gh-org/jenkinsflow-gh-folder-test/slow")

        # The job sleeps 10s
        assert (datetime.now() - before).total_seconds() >= 10


@pytest.mark.apis(ApiType.JENKINS)
def test_gh_folder_build_with_parameters(api_type):
    with api_select.api(__file__, api_type, existing_jobs=True) as api:
        api.flow_job()
        api.job("gh-org/jenkinsflow-gh-folder-test/parameters", max_fails=0, expect_invocations=1, expect_order=1)

        with serial(api, timeout=70, report_interval=1) as ctrl1:
            ctrl1.invoke("gh-org/jenkinsflow-gh-folder-test/parameters", GREETING="Hi")


@pytest.mark.apis(ApiType.JENKINS)
def test_gh_folder_scan_organization(api_type):
    with api_select.api(__file__, api_type, existing_jobs=True) as api:
        api.flow_job()
        api.job("gh-org", max_fails=0, expect_invocations=1, expect_order=1)

        # Scan time depends on the GitHub organization!
        with serial(api, timeout=10, report_interval=1) as ctrl1:
            ctrl1.invoke("gh-org", assume_finished_after=5)


@pytest.mark.apis(ApiType.JENKINS)
def test_gh_folder_scan_repo(api_type):
    with api_select.api(__file__, api_type, existing_jobs=True) as api:
        api.flow_job()
        api.job("gh-org/jenkinsflow-gh-folder-test", max_fails=0, expect_invocations=1, expect_order=1)

        # Repo scan time depends on the GitHub repo, it does not take too long, but can be queued for a while!
        with serial(api, timeout=10, report_interval=1) as ctrl1:
            ctrl1.invoke("gh-org/jenkinsflow-gh-folder-test", assume_finished_after=5)
