# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# NOTE: the tests here all raise exceptions because they can not really be run outside of a jenkinsjob
# TODO: Test that the script actually does what expected! The test here just assure that the script can be run :(

import os
import urllib2
import pytest
from pytest import raises, xfail

from jenkinsflow import set_build_result
from jenkinsflow.flow import serial, Propagation
from .framework import mock_api
from . import cfg as test_cfg

from demo_security import username, password

here = os.path.dirname(__file__)


@pytest.fixture
def pre_existing_cli(request):
    base_url = test_cfg.direct_url() + '/'
    cli_jar, base_url, public_base_url = set_build_result.cli_jar_info(base_url)
    if cli_jar is None:
        cli_jar = set_build_result.jenkins_cli_jar
    if not os.path.exists(cli_jar):
        set_build_result.download_cli(cli_jar, base_url, public_base_url)


@pytest.fixture
def no_pre_existing_cli(request):
    if os.path.exists(set_build_result.jenkins_cli_jar):
        os.remove(set_build_result.jenkins_cli_jar)
    if os.path.exists(set_build_result.hudson_cli_jar):
        os.remove(set_build_result.hudson_cli_jar)


def test_set_build_result_no_cli_jar(fake_java, no_pre_existing_cli, env_base_url, capfd):
    with mock_api.api(__file__) as api:
        try:
            api.flow_job()
            api.job('j1_fail', exec_time=0.01, max_fails=1, expect_invocations=1, expect_order=1)

            with serial(api, timeout=70, username=username, password=password, job_name_prefix=api.job_name_prefix, report_interval=3, propagation=Propagation.FAILURE_TO_UNSTABLE) as ctrl1:
                ctrl1.invoke('j1_fail')

        except urllib2.URLError:
            # Jenkins is not running, so we cant test this
            if not api.is_mocked:
                raise
            xfail()


def test_set_build_result(fake_java, pre_existing_cli, env_base_url, capfd):
    with mock_api.api(__file__) as api:
        try:
            api.flow_job()
            api.job('j1_fail', exec_time=0.01, max_fails=1, expect_invocations=1, expect_order=1)

            with serial(api, timeout=70, username=username, password=password, job_name_prefix=api.job_name_prefix, report_interval=3, propagation=Propagation.FAILURE_TO_UNSTABLE) as ctrl1:
                ctrl1.invoke('j1_fail')

        except urllib2.URLError:
            # Jenkins is not running, so we cant test this
            if not api.is_mocked:
                raise
            xfail()


def test_set_build_result_direct_url(fake_java, pre_existing_cli, env_base_url, capfd):
    with mock_api.api(__file__) as api:
        try:
            api.flow_job()
            api.job('j1_fail', exec_time=0.01, max_fails=1, expect_invocations=1, expect_order=1)

            with serial(api, timeout=70, username=username, password=password, job_name_prefix=api.job_name_prefix, report_interval=3,
                        propagation=Propagation.FAILURE_TO_UNSTABLE, direct_url=test_cfg.direct_url()) as ctrl1:
                ctrl1.invoke('j1_fail')

        except urllib2.URLError:
            # Jenkins is not running, so we cant test this
            if not api.is_mocked:
                raise
            xfail()


def test_set_build_result_no_auth(fake_java, pre_existing_cli, env_base_url, capfd):
    with mock_api.api(__file__) as api:
        try:
            api.flow_job()
            api.job('j1_fail', exec_time=0.01, max_fails=1, expect_invocations=1, expect_order=1)

            with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=3, propagation=Propagation.FAILURE_TO_UNSTABLE) as ctrl1:
                ctrl1.invoke('j1_fail')

        except urllib2.URLError:
            # Jenkins is not running, so we cant test this
            if not api.is_mocked:
                raise
            xfail()


def test_set_build_result_no_jenkinsurl(pre_existing_cli, env_no_base_url, capfd):
    with raises(Exception) as exinfo:
        with mock_api.api(__file__) as api:
            api.flow_job()
            api.job('j1_fail', exec_time=0.01, max_fails=1, expect_invocations=1, expect_order=1)

            with serial(api, timeout=70, username=username, password=password, job_name_prefix=api.job_name_prefix, report_interval=3, propagation=Propagation.FAILURE_TO_UNSTABLE) as ctrl1:
                ctrl1.invoke('j1_fail')

    assert "Could not get env variable JENKINS_URL or HUDSON_URL. Don't know whether to use jenkins-cli.jar or hudson-cli.jar for setting result! You must set 'Jenkins Location' in Jenkins setup for JENKINS_URL to be exported. You must set 'Hudson URL' in Hudson setup for HUDSON_URL to be exported." in exinfo.value.message


def test_set_build_result_call_script_direct_url(pre_existing_cli, capfd):
    with raises(SystemExit):
        set_build_result.main(['-h'])

    sout, _ = capfd.readouterr()
    assert '[--username' in sout
    assert '[--password' in sout
    assert '[--result' in sout
    assert '[--direct-url' in sout
    assert '[--java' in sout


def test_set_build_result_call_script_direct_url_trailing_slash(fake_java, pre_existing_cli, capfd):
    base_url = test_cfg.direct_url() + '/'
    set_build_result.main(['--direct-url', base_url])


def test_set_build_result_call_script_direct_url_no_trailing_slash(fake_java, pre_existing_cli, capfd):
    base_url = test_cfg.direct_url().rstrip('/')
    set_build_result.main(['--direct-url', base_url])
