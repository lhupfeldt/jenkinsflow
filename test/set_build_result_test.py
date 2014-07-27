# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# NOTE: the tests here all raise exceptions because they can not really be run outside of a jenkinsjob
# TODO: Test that the script actually does what expected! The test here just assure that the script can be run :(

import os, urllib2, re

import pytest
from pytest import raises, xfail, fixture  # pylint: disable=no-name-in-module

from jenkinsflow import set_build_result
from jenkinsflow.flow import serial, Propagation
from .framework import api_select
from .framework.utils import assert_lines_in
from . import cfg as test_cfg
from .cfg import ApiType

from demo_security import username, password

here = os.path.dirname(__file__)


def pre_existing_cli():
    if test_cfg.selected_api() == ApiType.SCRIPT:
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


def test_set_build_result_no_cli_jar(fake_java, env_base_url, capfd):
    with api_select.api(__file__) as api:
        no_pre_existing_cli()
        try:
            api.flow_job()
            api.job('j1_fail', exec_time=0.01, max_fails=1, expect_invocations=1, expect_order=1)

            with serial(api, timeout=70, username=username, password=password, job_name_prefix=api.job_name_prefix, report_interval=3,
                        propagation=Propagation.FAILURE_TO_UNSTABLE) as ctrl1:
                ctrl1.invoke('j1_fail')

        except urllib2.URLError:
            # Jenkins is not running, so we cant test this
            if api.api_type != ApiType.MOCK:
                raise
            xfail()

    sout, _ = capfd.readouterr()

    expected = [_setting_job_result_msg]
    if api.api_type != ApiType.SCRIPT:
        expected.append(re.compile("^INFO: Downloading cli: '%(public_url)s'$" % dict(public_url=test_cfg.public_cli_url())))
        assert '/jnlpJars/' in sout

    assert_lines_in(
        sout,
        *expected
    )


def test_set_build_result_no_cli_jar_env_base_url_trailing_slash(fake_java, env_base_url_trailing_slash, capfd):
    with api_select.api(__file__) as api:
        no_pre_existing_cli()
        try:
            api.flow_job()
            api.job('j1_fail', exec_time=0.01, max_fails=1, expect_invocations=1, expect_order=1)

            with serial(api, timeout=70, username=username, password=password, job_name_prefix=api.job_name_prefix, report_interval=3,
                        propagation=Propagation.FAILURE_TO_UNSTABLE) as ctrl1:
                ctrl1.invoke('j1_fail')

        except urllib2.URLError:
            # Jenkins is not running, so we cant test this
            if api.api_type != ApiType.MOCK:
                raise
            xfail()

    sout, _ = capfd.readouterr()

    expected = [_setting_job_result_msg]
    if api.api_type != ApiType.SCRIPT:
        expected.append(re.compile("^INFO: Downloading cli: '%(public_url)s'$" % dict(public_url=test_cfg.public_cli_url())))
        assert '/jnlpJars/' in sout

    assert_lines_in(
        sout,
        *expected
    )


def test_set_build_result_no_cli_jar_env_base_url_trailing_slashes(fake_java, env_base_url_trailing_slashes, capfd):
    with api_select.api(__file__) as api:
        no_pre_existing_cli()
        try:
            api.flow_job()
            api.job('j1_fail', exec_time=0.01, max_fails=1, expect_invocations=1, expect_order=1)

            with serial(api, timeout=70, username=username, password=password, job_name_prefix=api.job_name_prefix, report_interval=3,
                        propagation=Propagation.FAILURE_TO_UNSTABLE) as ctrl1:
                ctrl1.invoke('j1_fail')

        except urllib2.URLError:
            # Jenkins is not running, so we cant test this
            if api.api_type != ApiType.MOCK:
                raise
            xfail()

    sout, _ = capfd.readouterr()

    expected = [_setting_job_result_msg]
    if api.api_type != ApiType.SCRIPT:
        expected.append(re.compile("^INFO: Downloading cli: '%(public_url)s'$" % dict(public_url=test_cfg.public_cli_url())))
        assert '/jnlpJars/' in sout

    assert_lines_in(
        sout,
        *expected
    )


def test_set_build_result(fake_java, env_base_url):
    with api_select.api(__file__) as api:
        pre_existing_cli()
        try:
            api.flow_job()
            api.job('j1_fail', exec_time=0.01, max_fails=1, expect_invocations=1, expect_order=1)

            with serial(api, timeout=70, username=username, password=password, job_name_prefix=api.job_name_prefix, report_interval=3,
                        propagation=Propagation.FAILURE_TO_UNSTABLE) as ctrl1:
                ctrl1.invoke('j1_fail')

        except urllib2.URLError:
            # Jenkins is not running, so we cant test this
            if api.api_type != ApiType.MOCK:
                raise
            xfail()


def test_set_build_result_direct_url(fake_java, env_base_url):
    with api_select.api(__file__) as api:
        pre_existing_cli()
        try:
            api.flow_job()
            api.job('j1_fail', exec_time=0.01, max_fails=1, expect_invocations=1, expect_order=1)

            with serial(api, timeout=70, username=username, password=password, job_name_prefix=api.job_name_prefix, report_interval=3,
                        propagation=Propagation.FAILURE_TO_UNSTABLE, direct_url=test_cfg.direct_url()) as ctrl1:
                ctrl1.invoke('j1_fail')

        except urllib2.URLError:
            # Jenkins is not running, so we cant test this
            if api.api_type != ApiType.MOCK:
                raise
            xfail()


def test_set_build_result_no_cli_jar_env_base_url_eq_direct_url(fake_java, env_base_url, capfd):
    with api_select.api(__file__) as api:
        no_pre_existing_cli()
        try:
            api.flow_job()
            api.job('j1_fail', exec_time=0.01, max_fails=1, expect_invocations=1, expect_order=1)

            with serial(api, timeout=70, username=username, password=password, job_name_prefix=api.job_name_prefix, report_interval=3,
                        propagation=Propagation.FAILURE_TO_UNSTABLE, direct_url=test_cfg.public_url()) as ctrl1:
                ctrl1.invoke('j1_fail')

        except urllib2.URLError:
            # Jenkins is not running, so we cant test this
            if api.api_type != ApiType.MOCK:
                raise
            xfail()

    sout, _ = capfd.readouterr()

    expected = [_setting_job_result_msg]
    if api.api_type != ApiType.SCRIPT:
        expected.append(re.compile("^INFO: Downloading cli: '%(public_url)s'$" % dict(public_url=test_cfg.public_cli_url())))
        assert '/jnlpJars/' in sout

    assert_lines_in(
        sout,
        *expected
    )


def test_set_build_result_direct_url_trailing_slash(fake_java, env_base_url, capfd):
    with api_select.api(__file__) as api:
        pre_existing_cli()
        try:
            api.flow_job()
            api.job('j1_fail', exec_time=0.01, max_fails=1, expect_invocations=1, expect_order=1)

            with serial(api, timeout=70, username=username, password=password, job_name_prefix=api.job_name_prefix, report_interval=3,
                        propagation=Propagation.FAILURE_TO_UNSTABLE, direct_url=test_cfg.direct_url() + '/') as ctrl1:
                ctrl1.invoke('j1_fail')

        except urllib2.URLError:
            # Jenkins is not running, so we cant test this
            if api.api_type != ApiType.MOCK:
                raise
            xfail()

    sout, _ = capfd.readouterr()
    assert_lines_in(
        sout,
        "INFO: Setting job result to 'unstable'"
    )


def test_set_build_result_no_auth(fake_java, env_base_url):
    with api_select.api(__file__) as api:
        pre_existing_cli()
        try:
            api.flow_job()
            api.job('j1_fail', exec_time=0.01, max_fails=1, expect_invocations=1, expect_order=1)

            with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=3, propagation=Propagation.FAILURE_TO_UNSTABLE) as ctrl1:
                ctrl1.invoke('j1_fail')

        except urllib2.URLError:
            # Jenkins is not running, so we cant test this
            if api.api_type != ApiType.MOCK:
                raise
            xfail()


def test_set_build_result_no_jenkinsurl(env_no_base_url):
    if test_cfg.selected_api() == ApiType.SCRIPT:
        # JENKINS_URL is always set for script_api
        return

    with raises(Exception) as exinfo:
        with api_select.api(__file__) as api:
            pre_existing_cli()
            api.flow_job()
            api.job('j1_fail', exec_time=0.01, max_fails=1, expect_invocations=1, expect_order=1)

            with serial(api, timeout=70, username=username, password=password, job_name_prefix=api.job_name_prefix, report_interval=3,
                        propagation=Propagation.FAILURE_TO_UNSTABLE) as ctrl1:
                ctrl1.invoke('j1_fail')

    assert "Could not get env variable JENKINS_URL or HUDSON_URL. Don't know whether to use jenkins-cli.jar or hudson-cli.jar for setting result! You must set 'Jenkins Location' in Jenkins setup for JENKINS_URL to be exported. You must set 'Hudson URL' in Hudson setup for HUDSON_URL to be exported." in exinfo.value.message


def test_set_build_result_call_script_direct_url(capfd):
    with raises(SystemExit):
        with api_select.api(__file__):
            pre_existing_cli()
            set_build_result.main(['-h'])

    sout, _ = capfd.readouterr()
    assert '[--username' in sout
    assert '[--password' in sout
    assert '[--result' in sout
    assert '[--direct-url' in sout
    assert '[--java' in sout


def test_set_build_result_call_script_direct_url_trailing_slash(fake_java, env_base_url):
    with api_select.api(__file__):
        pre_existing_cli()
        base_url = test_cfg.direct_url() + '/'
        set_build_result.main(['--direct-url', base_url])


def test_set_build_result_call_script_direct_url_no_trailing_slash(fake_java, env_base_url):
    with api_select.api(__file__):
        pre_existing_cli()
        base_url = test_cfg.direct_url().rstrip('/')
        set_build_result.main(['--direct-url', base_url])
