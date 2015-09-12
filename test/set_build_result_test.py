# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# NOTE: the tests here all raise exceptions because they can not really be run outside of a jenkinsjob
# TODO: Test that the script actually does what expected! The test here just assure that the script can be run :(

import sys, os, urllib2, re, subprocess32
from os.path import join as jp

import pytest
from pytest import raises

from jenkinsflow import set_build_result
from jenkinsflow.flow import serial, Propagation
from jenkinsflow.cli.cli import cli

from .framework import api_select
from .framework.utils import assert_lines_in
from . import cfg as test_cfg
from .cfg import ApiType

from demo_security import username, password

here = os.path.abspath(os.path.dirname(__file__))


def pre_existing_cli():
    if test_cfg.selected_api() != ApiType.JENKINS:
        return

    public_base_url = os.environ.get('HUDSON_URL')
    cli_jar = set_build_result.hudson_cli_jar

    if public_base_url is None:
        public_base_url = os.environ.get('JENKINS_URL') or test_cfg.public_url()
        cli_jar = set_build_result.jenkins_cli_jar

    if not os.path.exists(cli_jar):
        set_build_result.download_cli(cli_jar, test_cfg.direct_url(), public_base_url)


def no_pre_existing_cli():
    if test_cfg.selected_api() == ApiType.SCRIPT:
        return

    if os.path.exists(set_build_result.jenkins_cli_jar):
        os.remove(set_build_result.jenkins_cli_jar)
    if os.path.exists(set_build_result.hudson_cli_jar):
        os.remove(set_build_result.hudson_cli_jar)


_setting_job_result_msg = "INFO: Setting job result to 'unstable'"


@pytest.mark.not_apis(ApiType.MOCK)
def test_set_build_result_no_cli_jar(fake_java, env_base_url, capfd):
    with api_select.api(__file__) as api:
        no_pre_existing_cli()
        api.flow_job()
        api.job('j1_fail', exec_time=0.01, max_fails=1, expect_invocations=1, expect_order=1)

        with serial(api, timeout=70, username=username, password=password, job_name_prefix=api.job_name_prefix, report_interval=3,
                    propagation=Propagation.FAILURE_TO_UNSTABLE) as ctrl1:
            ctrl1.invoke('j1_fail')

    sout, _ = capfd.readouterr()

    expected = [_setting_job_result_msg]
    if api.api_type != ApiType.SCRIPT:
        expected.append(re.compile("^INFO: Downloading cli: '%(public_url)s'$" % dict(public_url=test_cfg.public_cli_url())))
        assert '/jnlpJars/' in sout

    assert_lines_in(
        sout,
        *expected
    )


@pytest.mark.not_apis(ApiType.MOCK)
def test_set_build_result_no_cli_jar_env_base_url_trailing_slash(fake_java, env_base_url_trailing_slash, capfd):
    with api_select.api(__file__) as api:
        no_pre_existing_cli()
        api.flow_job()
        api.job('j1_fail', exec_time=0.01, max_fails=1, expect_invocations=1, expect_order=1)

        with serial(api, timeout=70, username=username, password=password, job_name_prefix=api.job_name_prefix, report_interval=3,
                    propagation=Propagation.FAILURE_TO_UNSTABLE) as ctrl1:
            ctrl1.invoke('j1_fail')

    sout, _ = capfd.readouterr()

    expected = [_setting_job_result_msg]
    if api.api_type != ApiType.SCRIPT:
        expected.append(re.compile("^INFO: Downloading cli: '%(public_url)s'$" % dict(public_url=test_cfg.public_cli_url())))
        assert '/jnlpJars/' in sout

    assert_lines_in(
        sout,
        *expected
    )


@pytest.mark.not_apis(ApiType.MOCK)
def test_set_build_result_no_cli_jar_env_base_url_trailing_slashes(fake_java, env_base_url_trailing_slashes, capfd):
    with api_select.api(__file__) as api:
        no_pre_existing_cli()
        api.flow_job()
        api.job('j1_fail', exec_time=0.01, max_fails=1, expect_invocations=1, expect_order=1)

        with serial(api, timeout=70, username=username, password=password, job_name_prefix=api.job_name_prefix, report_interval=3,
                    propagation=Propagation.FAILURE_TO_UNSTABLE) as ctrl1:
            ctrl1.invoke('j1_fail')

    sout, _ = capfd.readouterr()

    expected = [_setting_job_result_msg]
    if api.api_type != ApiType.SCRIPT:
        expected.append(re.compile("^INFO: Downloading cli: '%(public_url)s'$" % dict(public_url=test_cfg.public_cli_url())))
        assert '/jnlpJars/' in sout

    assert_lines_in(
        sout,
        *expected
    )


@pytest.mark.not_apis(ApiType.MOCK)
def test_set_build_result(fake_java, env_base_url):
    with api_select.api(__file__) as api:
        pre_existing_cli()
        api.flow_job()
        api.job('j1_fail', exec_time=0.01, max_fails=1, expect_invocations=1, expect_order=1)

        with serial(api, timeout=70, username=username, password=password, job_name_prefix=api.job_name_prefix, report_interval=3,
                    propagation=Propagation.FAILURE_TO_UNSTABLE) as ctrl1:
            ctrl1.invoke('j1_fail')


@pytest.mark.not_apis(ApiType.MOCK)
def test_set_build_result_direct_url(fake_java, env_base_url):
    with api_select.api(__file__) as api:
        pre_existing_cli()
        api.flow_job()
        api.job('j1_fail', exec_time=0.01, max_fails=1, expect_invocations=1, expect_order=1)

        with serial(api, timeout=70, username=username, password=password, job_name_prefix=api.job_name_prefix, report_interval=3,
                    propagation=Propagation.FAILURE_TO_UNSTABLE, direct_url=test_cfg.direct_url()) as ctrl1:
            ctrl1.invoke('j1_fail')


@pytest.mark.not_apis(ApiType.MOCK)
def test_set_build_result_no_cli_jar_env_base_url_eq_direct_url(fake_java, env_base_url, capfd):
    with api_select.api(__file__) as api:
        no_pre_existing_cli()
        api.flow_job()
        api.job('j1_fail', exec_time=0.01, max_fails=1, expect_invocations=1, expect_order=1)

        with serial(api, timeout=70, username=username, password=password, job_name_prefix=api.job_name_prefix, report_interval=3,
                    propagation=Propagation.FAILURE_TO_UNSTABLE, direct_url=test_cfg.public_url()) as ctrl1:
            ctrl1.invoke('j1_fail')

    sout, _ = capfd.readouterr()

    expected = [_setting_job_result_msg]
    if api.api_type != ApiType.SCRIPT:
        expected.append(re.compile("^INFO: Downloading cli: '%(public_url)s'$" % dict(public_url=test_cfg.public_cli_url())))
        expected.append("^INFO: Download finished: ")
        assert '/jnlpJars/' in sout

    assert_lines_in(
        sout,
        *expected
    )


@pytest.mark.not_apis(ApiType.MOCK)
def test_set_build_result_direct_url_trailing_slash(fake_java, env_base_url, capfd):
    with api_select.api(__file__) as api:
        pre_existing_cli()
        api.flow_job()
        api.job('j1_fail', exec_time=0.01, max_fails=1, expect_invocations=1, expect_order=1)

        with serial(api, timeout=70, username=username, password=password, job_name_prefix=api.job_name_prefix, report_interval=3,
                    propagation=Propagation.FAILURE_TO_UNSTABLE, direct_url=test_cfg.direct_url() + '/') as ctrl1:
            ctrl1.invoke('j1_fail')

    sout, _ = capfd.readouterr()
    assert_lines_in(
        sout,
        _setting_job_result_msg
    )


@pytest.mark.not_apis(ApiType.MOCK)
def test_set_build_result_direct_url_different_from_proxied_url(fake_java, env_different_base_url, capfd):
    with api_select.api(__file__) as api:
        no_pre_existing_cli()
        api.flow_job()
        api.job('j1_fail', exec_time=0.01, max_fails=1, expect_invocations=1, expect_order=1)

        with serial(api, timeout=70, username=username, password=password, job_name_prefix=api.job_name_prefix, report_interval=3,
                    propagation=Propagation.FAILURE_TO_UNSTABLE, direct_url=test_cfg.direct_url() + '/') as ctrl1:
            ctrl1.invoke('j1_fail')

    sout, _ = capfd.readouterr()

    expected = [_setting_job_result_msg]
    if api.api_type != ApiType.SCRIPT:
        public_url = test_cfg.proxied_public_cli_url()
        direct_url = test_cfg.direct_cli_url()
        expected.append("^INFO: Downloading cli: '%(public_url)s' (using direct url: %(direct_url)s)" % \
                        dict(public_url=public_url, direct_url=direct_url))

    assert_lines_in(
        sout,
        *expected
    )


@pytest.mark.not_apis(ApiType.MOCK)
def test_set_build_result_no_auth(fake_java, env_base_url):
    with api_select.api(__file__) as api:
        pre_existing_cli()
        api.flow_job()
        api.job('j1_fail', exec_time=0.01, max_fails=1, expect_invocations=1, expect_order=1)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=3, propagation=Propagation.FAILURE_TO_UNSTABLE) as ctrl1:
            ctrl1.invoke('j1_fail')


@pytest.mark.not_apis(ApiType.SCRIPT)  # JENKINS_URL is always set for script_api
def test_set_build_result_no_jenkinsurl(env_no_base_url):
    with raises(Exception) as exinfo:
        with api_select.api(__file__) as api:
            api.flow_job()
            api.job('j1_fail', exec_time=0.01, max_fails=1, expect_invocations=1, expect_order=1)

            with serial(api, timeout=70, username=username, password=password, job_name_prefix=api.job_name_prefix, report_interval=3,
                        propagation=Propagation.FAILURE_TO_UNSTABLE) as ctrl1:
                ctrl1.invoke('j1_fail')

    assert_lines_in(
        exinfo.value.message,
        "Could not get env variable JENKINS_URL or HUDSON_URL. You must set 'Jenkins Location' in Jenkins setup for JENKINS_URL to be exported. You must set 'Hudson URL' in Hudson setup for HUDSON_URL to be exported."
    )


@pytest.mark.not_apis(ApiType.MOCK)
def test_set_build_result_call_cli_direct_url_trailing_slash(fake_java, env_base_url, cli_runner):
    with api_select.api(__file__):
        pre_existing_cli()
        base_url = test_cfg.direct_url() + '/'
        _result = cli_runner.invoke(cli, ['set_build_result', '--direct-url', base_url])


@pytest.mark.not_apis(ApiType.MOCK)
def test_set_build_result_call_main_direct_url_no_trailing_slash(fake_java, env_base_url, cli_runner):
    with api_select.api(__file__):
        pre_existing_cli()
        base_url = test_cfg.direct_url().rstrip('/')
        _result = cli_runner.invoke(cli, ['set_build_result', '--direct-url', base_url])


def test_set_build_result_call_script_help(capfd):
    # Invoke this in a subprocess to ensure that calling the script works
    # This will not give coverage as it not not traced through the subprocess call
    rc = subprocess32.call([sys.executable, jp(here, '../cli/cli.py'), 'set_build_result', '--help'])
    assert rc == 0

    sout, _ = capfd.readouterr()
    assert '--result' in sout
    assert '--direct-url' in sout
    assert '--username' in sout
    assert '--password' in sout
    assert '--java' in sout
