#!/usr/bin/python

# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# NOTE: the tests here all raise exceptions because they can not really be run outside of a jenkinsjob
# TODO: Test that the script actually does what expected! The test here just assure that the script can be run :(

from __future__ import print_function

import os
from os.path import join as jp
import subprocess
import pytest
from pytest import raises, xfail

from jenkinsflow import set_build_result
from jenkinsflow.flow import serial
from framework import mock_api

from demo_security import username, password

here = os.path.dirname(__file__)

def _set_unset_env_fixture(var_name, not_set_value, request):
    has_url = os.environ.get(var_name)
    if not has_url:
        os.environ[var_name] = not_set_value
    def fin():
        if not has_url:
            del os.environ[var_name]
    request.addfinalizer(fin)


@pytest.fixture
def env_build_url(request):
    # Fake that we are running from inside jenkins job
    _set_unset_env_fixture('BUILD_URL', 'http://localhost:8080/job/not_there', request)


@pytest.fixture
def env_base_url(request):
    # Fake that we are running from inside jenkins job
    _set_unset_env_fixture('JENKINS_URL', 'http://localhost:8080', request)
    _set_unset_env_fixture('HUDSON_URL', 'http://localhost:8080', request)


@pytest.fixture
def pre_existing_cli(request):
    has_url = os.environ.get('JENKINS_URL') or os.environ.get('HUDSON_URL')
    if not has_url:
        os.environ['JENKINS_URL'] = 'http://localhost:8080'
    if not os.path.exists(set_build_result.cli_jar):
        set_build_result.download_cli()
    if not has_url:
        del os.environ['JENKINS_URL']


@pytest.fixture
def no_pre_existing_cli(request):
    if os.path.exists(set_build_result.cli_jar):
        os.remove(set_build_result.cli_jar)


def test_set_build_result(env_build_url, env_base_url, pre_existing_cli, capfd):
    with raises(subprocess.CalledProcessError):
        with mock_api.api(__file__) as api:
            api.flow_job()
            api.job('j1_fail', exec_time=0.5, max_fails=1, expect_invocations=1, expect_order=1)

            with serial(api, timeout=70, username=username, password=password, job_name_prefix=api.job_name_prefix, report_interval=3, warn_only=True) as ctrl1:
                ctrl1.invoke('j1_fail')

        _, serr = capfd.readouterr()
        assert "java.io.IOException: There's no Jenkins running at http://localhost:8080/job/not_there/" in serr


def test_set_build_result_no_auth(env_build_url, env_base_url, pre_existing_cli, capfd):
    with raises(subprocess.CalledProcessError):
        with mock_api.api(__file__) as api:
            api.flow_job()
            api.job('j1_fail', exec_time=0.5, max_fails=1, expect_invocations=1, expect_order=1)

            with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=3, warn_only=True) as ctrl1:
                ctrl1.invoke('j1_fail')

        _, serr = capfd.readouterr()
        assert "java.io.IOException: There's no Jenkins running at http://localhost:8080/job/not_there/" in serr


def test_set_build_result_no_jenkinsurl(env_build_url, pre_existing_cli, capfd):
    with raises(Exception) as exinfo:
        with mock_api.api(__file__) as api:
            api.flow_job()
            api.job('j1_fail', exec_time=0.5, max_fails=1, expect_invocations=1, expect_order=1)

            with serial(api, timeout=70, username=username, password=password, job_name_prefix=api.job_name_prefix, report_interval=3, warn_only=True) as ctrl1:
                ctrl1.invoke('j1_fail')

    assert "Could not get env variable JENKINS_URL or HUDSON_URL. Don't know how to download jenkins-cli.jar needed for setting result!" in exinfo.value.message


def test_set_build_result_no_build_url(pre_existing_cli, capfd):
    with mock_api.api(__file__) as api:
        api.flow_job()
        api.job('j1_fail', exec_time=0.5, max_fails=1, expect_invocations=1, expect_order=1)
    
        with serial(api, timeout=70, username=username, password=password, job_name_prefix=api.job_name_prefix, report_interval=3, warn_only=True) as ctrl1:
            ctrl1.invoke('j1_fail')
    
    sout, serr = capfd.readouterr()
    assert "INFO: Not running inside Jenkins or Hudson job, no job to set result 'unstable' for!" in serr


def test_set_build_result_call_script(pre_existing_cli, capfd):
    with raises(SystemExit):
        set_build_result.main(['--username', 'dummy', '--password', 'dummy', '-h'])
