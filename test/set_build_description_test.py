# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import sys, os, urllib2, re, subprocess32
from os.path import join as jp

from pytest import raises

from jenkinsflow.flow import serial
from .framework import api_select
from . import cfg as test_cfg
from .cfg import ApiType

from demo_security import username, password


_here = os.path.dirname(os.path.abspath(__file__))


def test_set_build_description_flow_set():
    with api_select.api(__file__, login=True) as api:
        api.flow_job()
        _params = (('password', '', 'Some password'), ('s1', '', 'Some string argument'))
        api.job('job-1', exec_time=0.01, max_fails=0, expect_invocations=1, expect_order=1, params=_params)
        api.job('job-2', exec_time=0.01, max_fails=0, expect_invocations=1, expect_order=2, params=_params, serial=True)
        api.job('job-3', exec_time=0.01, max_fails=0, expect_invocations=1, expect_order=3, params=_params)
        api.job('job-4', exec_time=0.01, max_fails=0, expect_invocations=1, expect_order=3, params=_params)
        api.job('job-5', exec_time=0.01, max_fails=0, expect_invocations=1, expect_order=3, params=_params)
        api.job('job-6', exec_time=0.01, max_fails=0, expect_invocations=1, expect_order=4, params=_params)
        api.job('job-7', exec_time=0.01, max_fails=0, expect_invocations=1, expect_order=5, params=_params, serial=True)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=1, description="AAA") as ctrl1:
            ctrl1.invoke('job-1', password='a', s1='b')
            ctrl1.invoke('job-2', password='a', s1='b')

            with ctrl1.parallel(timeout=40, report_interval=3) as ctrl2:
                with ctrl2.serial(timeout=40, report_interval=3) as ctrl3a:
                    ctrl3a.invoke('job-3', password='a', s1='b')
                    ctrl3a.invoke('job-6', password='a', s1='b')

                with ctrl2.parallel(timeout=40, report_interval=3) as ctrl3b:
                    ctrl3b.invoke('job-4', password='a', s1='b')
                    ctrl3b.invoke('job-5', password='a', s1='b')

            ctrl1.invoke('job-7', password='a', s1='b')

        # TODO read description back to validate that it was set!


def test_set_build_description_util():
    with api_select.api(__file__, login=True) as api:
        api.flow_job()
        job_name = 'job-1'
        api.job(job_name, exec_time=0.01, max_fails=0, expect_invocations=1, expect_order=1)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=1, description="AAA") as ctrl1:
            ctrl1.invoke(job_name, password='a', s1='b')

        # Need to read the build number
        job = api.get_job(api.job_name_prefix + job_name)
        _, _, build_num = job.job_status()

        from jenkinsflow.set_build_description import set_build_description

        set_build_description(api, job.name, build_num, 'BBB1')
        set_build_description(api, job.name, build_num, 'BBB2', replace=False)
        set_build_description(api, job.name, build_num, 'BBB3', replace=True)
        set_build_description(api, job.name, build_num, 'BBB4', replace=False, separator='#')
        set_build_description(api, job.name, build_num, 'BBB5', separator='!!')

        # TODO read back description and verify


def test_set_build_description_call_main():
    with api_select.api(__file__, login=True) as api:
        if api.api_type == ApiType.MOCK:
            return

        api.flow_job()
        job_name = 'job-1'
        api.job(job_name, exec_time=0.01, max_fails=0, expect_invocations=1, expect_order=1)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=1) as ctrl1:
            ctrl1.invoke(job_name, password='a', s1='b')

        # Need to read the build number
        job = api.get_job(api.job_name_prefix + job_name)
        _, _, build_num = job.job_status()

        from jenkinsflow.set_build_description import main

        base_url = test_cfg.direct_url() + '/'
        main(['--job-name', job.name,
              '--build-number', repr(build_num),
              '--description', 'BBB1',
              '--direct-url', base_url,
              '--separator', '\n',
              '--username', username,
              '--password', password])

        main(['--job-name', job.name,
              '--build-number', repr(build_num),
              '--description', 'BBB2',
              '--direct-url', base_url,
              '--replace', 
              '--username', username,
              '--password', password])

        # TODO read back description and verify


def test_set_build_description_env_url(env_base_url):
    with api_select.api(__file__, login=True) as api:
        if api.api_type == ApiType.MOCK:
            return

        api.flow_job()
        job_name = 'j1'
        api.job(job_name, exec_time=0.01, max_fails=0, expect_invocations=1, expect_order=1)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=1) as ctrl1:
            ctrl1.invoke(job_name, password='a', s1='b')

        # Need to read the build number
        job = api.get_job(api.job_name_prefix + job_name)
        _, _, build_num = job.job_status()

        from jenkinsflow.set_build_description import main

        main(['--job-name', job.name,
              '--build-number', repr(build_num),
              '--description', 'BBB1',
              '--separator', '\n',
              '--username', username,
              '--password', password])

        # TODO read back description and verify


def test_set_build_description_no_env_url(capsys, env_no_base_url):
    with api_select.api(__file__, login=True) as api:
        if api.api_type in (ApiType.MOCK, ApiType.SCRIPT):
            return

        api.flow_job()
        job_name = 'j1'
        api.job(job_name, exec_time=0.01, max_fails=0, expect_invocations=1, expect_order=1)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=1) as ctrl1:
            ctrl1.invoke(job_name, password='a', s1='b')

        # Need to read the build number
        job = api.get_job(api.job_name_prefix + job_name)
        _, _, build_num = job.job_status()

        from jenkinsflow.set_build_description import main

        with raises(Exception) as exinfo:
            main(['--job-name', job.name, '--build-number', repr(build_num), '--description', 'BBB1'])

        assert "Could not get env variable JENKINS_URL or HUDSON_URL" in exinfo.value.message
        _, serr = capsys.readouterr()
        assert "You must specify '--direct-url'" in serr


def test_set_build_result_call_script_help(capfd):
    # Invoke this in a subprocess to ensure that calling the script works
    # This will not give coverage as it not not traced through the subprocess call
    rc = subprocess32.call([sys.executable, jp(_here, '..', 'set_build_description.py'), '--help'])
    assert rc == 0

    sout, _ = capfd.readouterr()
    assert '[--job-name'
    assert '[--build-number'
    assert '[--description'
    assert '[--direct-url' in sout
    assert '[--replace' in sout
    assert '--separator' in sout
    assert '[(--username <user_name> --password <password>)]' in sout
