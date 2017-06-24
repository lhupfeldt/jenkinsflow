# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# NOTE: the tests here all raise exceptions because they can not really be run outside of a jenkinsjob
# TODO: Test that the script actually does what expected! The test here just assure that the script can be run :(

import sys, os, re
major_version = sys.version_info.major
if major_version < 3:
    import subprocess32 as subprocess
    import urllib2 as urllib
else:
    import subprocess, urllib

from os.path import join as jp

import pytest
from pytest import raises

from jenkinsflow.flow import serial, Propagation, BuildResult
from jenkinsflow.cli.cli import cli

from .framework import api_select
from .framework.utils import lines_in, jenkins_cli_jar, hudson_cli_jar
from . import cfg as test_cfg
from .cfg import ApiType

from demo_security import username, password

here = os.path.abspath(os.path.dirname(__file__))


def _download_cli_jar(cli_jar, direct_base_url, public_base_url):
    if major_version < 3:
        from urllib2 import urlopen
        save_mode = 'w'
    else:
        from urllib.request import urlopen
        save_mode = 'w+b'

    path = '/jnlpJars/' + cli_jar
    if direct_base_url and direct_base_url != public_base_url:
        download_cli_url = direct_base_url + path
        print("Prereqs: Downloading cli:", repr(public_base_url + path), "(using direct url:", download_cli_url + ')')
    else:
        download_cli_url = public_base_url + path
        print("Prereqs: Downloading cli:", repr(download_cli_url))

    response = urlopen(download_cli_url)
    with open(cli_jar, save_mode) as ff:
        ff.write(response.read())
    print("Prereqs: Download finished:", repr(cli_jar))


def pre_existing_cli_jar(api_type):
    if api_type != ApiType.JENKINS:
        return

    public_base_url = os.environ.get('HUDSON_URL')
    cli_jar = hudson_cli_jar

    if public_base_url is None:
        public_base_url = test_cfg.public_url(api_type)
        cli_jar = jenkins_cli_jar

    if not os.path.exists(cli_jar):
        _download_cli_jar(cli_jar, test_cfg.direct_url(api_type), public_base_url)


def no_pre_existing_cli_jar(api_type):
    if api_type == ApiType.SCRIPT:
        return

    if os.path.exists(jenkins_cli_jar):
        os.remove(jenkins_cli_jar)
    if os.path.exists(hudson_cli_jar):
        os.remove(hudson_cli_jar)


_setting_job_result_msg = "INFO: Setting job result to 'unstable'"


def _download_same_url(download_url):
    return "^INFO: Downloading cli: {download_url!r}".format(download_url=download_url)


def _download_different_urls(api_type):
    return "^INFO: Downloading cli: {public_url!r} (using direct url: {direct_url!r})".format(
        public_url=test_cfg.proxied_public_cli_url(api_type), direct_url=test_cfg.direct_cli_url(api_type))


@pytest.mark.not_apis(ApiType.MOCK)
def test_set_build_result_no_cli_jar(api_type, fake_java, env_base_url, capfd):
    with api_select.api(__file__, api_type, fake_public_uri=test_cfg.direct_url(api_type)) as api:
        no_pre_existing_cli_jar(api_type)
        api.flow_job()
        api.job('j1_fail', max_fails=1, expect_invocations=1, expect_order=1)

        with serial(api, timeout=70, username=username, password=password, job_name_prefix=api.job_name_prefix, report_interval=3,
                    propagation=Propagation.FAILURE_TO_UNSTABLE) as ctrl1:
            ctrl1.invoke('j1_fail')

    sout, _ = capfd.readouterr()

    expected = [_setting_job_result_msg]
    if api.api_type != ApiType.SCRIPT:
        expected.append(_download_same_url(test_cfg.direct_cli_url(api_type)))
        assert '/jnlpJars/' in sout

    assert lines_in(
        api_type, sout,
        *expected
    )


@pytest.mark.not_apis(ApiType.MOCK)
def test_set_build_result_no_cli_jar_env_base_url_trailing_slash(api_type, fake_java, env_base_url_trailing_slash, capfd):
    with api_select.api(__file__, api_type, fake_public_uri=test_cfg.direct_url(api_type) + '/') as api:
        no_pre_existing_cli_jar(api_type)
        api.flow_job()
        api.job('j1_fail', max_fails=1, expect_invocations=1, expect_order=1)

        with serial(api, timeout=70, username=username, password=password, job_name_prefix=api.job_name_prefix, report_interval=3,
                    propagation=Propagation.FAILURE_TO_UNSTABLE) as ctrl1:
            ctrl1.invoke('j1_fail')

    sout, _ = capfd.readouterr()

    expected = [_setting_job_result_msg]
    if api.api_type != ApiType.SCRIPT:
        expected.append(_download_same_url(test_cfg.direct_cli_url(api_type)))
        assert '/jnlpJars/' in sout

    assert lines_in(
        api_type, sout,
        *expected
    )


@pytest.mark.not_apis(ApiType.MOCK)
def test_set_build_result_no_cli_jar_env_base_url_trailing_slashes(api_type, fake_java, capfd):
    with api_select.api(__file__, api_type, fake_public_uri=test_cfg.direct_url(api_type) + '//') as api:
        no_pre_existing_cli_jar(api_type)
        api.flow_job()
        api.job('j1_fail', max_fails=1, expect_invocations=1, expect_order=1)

        with serial(api, timeout=70, username=username, password=password, job_name_prefix=api.job_name_prefix, report_interval=3,
                    propagation=Propagation.FAILURE_TO_UNSTABLE) as ctrl1:
            ctrl1.invoke('j1_fail')

    sout, _ = capfd.readouterr()

    expected = [_setting_job_result_msg]
    if api.api_type != ApiType.SCRIPT:
        expected.append(_download_same_url(test_cfg.direct_cli_url(api_type)))
        assert '/jnlpJars/' in sout

    assert lines_in(
        api_type, sout,
        *expected
    )


@pytest.mark.not_apis(ApiType.MOCK)
def test_set_build_result(api_type, fake_java):
    with api_select.api(__file__, api_type) as api:
        pre_existing_cli_jar(api_type)
        api.flow_job()
        api.job('j1_fail', max_fails=1, expect_invocations=1, expect_order=1)

        with serial(api, timeout=70, username=username, password=password, job_name_prefix=api.job_name_prefix, report_interval=3,
                    propagation=Propagation.FAILURE_TO_UNSTABLE) as ctrl1:
            ctrl1.invoke('j1_fail')


@pytest.mark.not_apis(ApiType.MOCK)
def test_set_build_result_direct_url(api_type, fake_java):
    with api_select.api(__file__, api_type) as api:
        pre_existing_cli_jar(api_type)
        api.flow_job()
        api.job('j1_fail', max_fails=1, expect_invocations=1, expect_order=1)

        with serial(api, timeout=70, username=username, password=password, job_name_prefix=api.job_name_prefix, report_interval=3,
                    propagation=Propagation.FAILURE_TO_UNSTABLE, direct_url=test_cfg.direct_url(api_type)) as ctrl1:
            ctrl1.invoke('j1_fail')


@pytest.mark.not_apis(ApiType.MOCK)
def test_set_build_result_no_cli_jar_env_base_url_eq_direct_url(api_type, fake_java, env_base_url, capfd):
    with api_select.api(__file__, api_type, fake_public_uri=test_cfg.direct_url(api_type)) as api:
        no_pre_existing_cli_jar(api_type)
        api.flow_job()
        api.job('j1_fail', max_fails=1, expect_invocations=1, expect_order=1)

        with serial(api, timeout=70, username=username, password=password, job_name_prefix=api.job_name_prefix, report_interval=3,
                    propagation=Propagation.FAILURE_TO_UNSTABLE, direct_url=test_cfg.public_url(api_type)) as ctrl1:
            ctrl1.invoke('j1_fail')

    sout, _ = capfd.readouterr()

    expected = [_setting_job_result_msg]
    if api.api_type != ApiType.SCRIPT:
        expected.append(re.compile(_download_same_url(test_cfg.direct_cli_url(api_type)) + '$'))
        expected.append("^INFO: Download finished: ")
        assert '/jnlpJars/' in sout

    assert lines_in(
        api_type, sout,
        *expected
    )


@pytest.mark.not_apis(ApiType.MOCK)
def test_set_build_result_direct_url_trailing_slash(api_type, fake_java, env_base_url, capfd):
    with api_select.api(__file__, api_type) as api:
        pre_existing_cli_jar(api_type)
        api.flow_job()
        api.job('j1_fail', max_fails=1, expect_invocations=1, expect_order=1)

        with serial(api, timeout=70, username=username, password=password, job_name_prefix=api.job_name_prefix, report_interval=3,
                    propagation=Propagation.FAILURE_TO_UNSTABLE, direct_url=test_cfg.direct_url(api_type) + '/') as ctrl1:
            ctrl1.invoke('j1_fail')

    sout, _ = capfd.readouterr()
    assert lines_in(
        api_type, sout,
        _setting_job_result_msg
    )


@pytest.mark.not_apis(ApiType.MOCK)
def test_set_build_result_direct_url_different_from_proxied_url(api_type, fake_java, capfd):
    with api_select.api(__file__, api_type, fake_public_uri=test_cfg.proxied_public_url) as api:
        no_pre_existing_cli_jar(api_type)
        api.flow_job()
        api.job('j1_fail', max_fails=1, expect_invocations=1, expect_order=1)

        with serial(api, timeout=70, username=username, password=password, job_name_prefix=api.job_name_prefix, report_interval=3,
                    propagation=Propagation.FAILURE_TO_UNSTABLE, direct_url=test_cfg.direct_url(api_type) + '/') as ctrl1:
            ctrl1.invoke('j1_fail')

    sout, _ = capfd.readouterr()

    expected = [_setting_job_result_msg]
    if api.api_type != ApiType.SCRIPT:
        expected.append(_download_different_urls(api_type))

    assert lines_in(
        api_type, sout,
        *expected
    )


@pytest.mark.not_apis(ApiType.MOCK)
def test_set_build_result_no_auth(api_type, fake_java, env_base_url):
    with api_select.api(__file__, api_type) as api:
        pre_existing_cli_jar(api_type)
        api.flow_job()
        api.job('j1_fail', max_fails=1, expect_invocations=1, expect_order=1)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=3, propagation=Propagation.FAILURE_TO_UNSTABLE) as ctrl1:
            ctrl1.invoke('j1_fail')


@pytest.mark.apis(ApiType.SCRIPT)
def test_set_build_result_unstable_script_api(api_type):
    with api_select.api(__file__, api_type) as api:
        api.flow_job()
        api.job('j11_unstable', max_fails=0, expect_invocations=1, expect_order=1, final_result='UNSTABLE', final_result_use_cli=True)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix) as ctrl1:
            ctrl1.invoke('j11_unstable')

        assert ctrl1.result == BuildResult.UNSTABLE


@pytest.mark.not_apis(ApiType.SCRIPT)  # JENKINS_URL is always set for script_api
def test_set_build_result_no_jenkinsurl(api_type, fake_java, env_no_base_url, cli_runner):
    with api_select.api(__file__, api_type):
        pre_existing_cli_jar(api_type)
        result = cli_runner.invoke(cli, ['set_build_result'])

    assert result.exit_code != 0
    assert result.exception

    assert lines_in(
        api_type, str(result.exception),
        "Could not get env variable JENKINS_URL or HUDSON_URL. You must set 'Jenkins Location' in Jenkins setup for JENKINS_URL to be exported. You must set 'Hudson URL' in Hudson setup for HUDSON_URL to be exported."
    )


@pytest.mark.not_apis(ApiType.MOCK, ApiType.SCRIPT)
def test_set_build_result_call_cli_direct_url_trailing_slash(api_type, fake_java, env_base_url, cli_runner):
    with api_select.api(__file__, api_type) as api:
        pre_existing_cli_jar(api_type)
        base_url = test_cfg.direct_url(api_type) + '/'

        api.flow_job()
        api.job('j1_unstable', max_fails=0, expect_invocations=1, expect_order=1,
                final_result='UNSTABLE', final_result_use_cli=True, set_build_result_use_url=base_url)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix) as ctrl1:
            ctrl1.invoke('j1_unstable')

        assert ctrl1.result == BuildResult.UNSTABLE


@pytest.mark.apis(ApiType.SCRIPT)
def test_set_build_result_call_cli_direct_url_trailing_slash_script_api(api_type, env_base_url, cli_runner):
    with api_select.api(__file__, api_type):
        pre_existing_cli_jar(api_type)
        base_url = test_cfg.direct_url(api_type) + '/'
        result = cli_runner.invoke(cli, ['set_build_result', '--direct-url', base_url])

    assert result.exit_code != 0
    assert result.exception

    assert lines_in(
        api_type, str(result.exception),
        "Could not get EXECUTOR_NUMBER from env. 'set_build_result' must be invoked from within a running job"
    )


@pytest.mark.not_apis(ApiType.MOCK, ApiType.SCRIPT)
def test_set_build_result_call_main_direct_url_no_trailing_slash(api_type, fake_java, env_base_url, cli_runner):
    with api_select.api(__file__, api_type) as api:
        pre_existing_cli_jar(api_type)
        base_url = test_cfg.direct_url(api_type).rstrip('/')

        api.flow_job()
        api.job('j1_unstable', max_fails=0, expect_invocations=1, expect_order=1,
                final_result='UNSTABLE', final_result_use_cli=True, set_build_result_use_url=base_url)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix) as ctrl1:
            ctrl1.invoke('j1_unstable')

        assert ctrl1.result == BuildResult.UNSTABLE


def test_set_build_result_call_script_help(capfd):
    # Invoke this in a subprocess to ensure that calling the script works
    # This will not give coverage as it not not traced through the subprocess call
    rc = subprocess.call([sys.executable, jp(here, '../cli/cli.py'), 'set_build_result', '--help'])
    assert rc == 0

    sout, _ = capfd.readouterr()
    assert '--result' in sout
    assert '--direct-url' in sout
    assert '--username' in sout
    assert '--password' in sout
    assert '--java' in sout
