#!/usr/bin/python

# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from jenkinsflow.flow import serial, parallel
from framework import mock_api


def test_empty_flow_top_level_serial():
    with mock_api.api(__file__) as api:
        api.flow_job()

        with serial(api, timeout=70):
            pass


def test_empty_flow_top_level_parallel():
    with mock_api.api(__file__) as api:
        api.flow_job()

        with parallel(api, timeout=70):
            pass


def test_empty_flow_serial_parallel():
    with mock_api.api(__file__) as api:
        api.flow_job()
        api.job('j1', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j2', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=2)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=1) as ctrl1:
            ctrl1.invoke('j1')
            with ctrl1.parallel():
                pass
            ctrl1.invoke('j2')


def test_empty_flow_parallel_serial():
    with mock_api.api(__file__) as api:
        api.flow_job()
        api.job('j1', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j2', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=1)

        with parallel(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=1) as ctrl1:
            ctrl1.invoke('j1')
            with ctrl1.serial():
                pass
            ctrl1.invoke('j2')


def test_empty_flow_mix():
    with mock_api.api(__file__) as api:
        api.flow_job()
        api.job('j11', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j31', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=2)
        api.job('j32', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=3)
        api.job('j12', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=4)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=1) as ctrl1:
            ctrl1.invoke('j11')

            with ctrl1.parallel():
                pass

            with ctrl1.serial():
                pass

            with ctrl1.parallel() as ctrl2:
                with ctrl2.serial() as ctrl3a:
                    ctrl3a.invoke('j31')
                    ctrl3a.invoke('j32')

                with ctrl2.parallel():
                    pass

            ctrl1.invoke('j12')
