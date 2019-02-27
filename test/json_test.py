# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import os
from os.path import join as jp
import re

from jenkinsflow.flow import serial

from .framework import api_select, utils
from .framework.utils import flow_graph_dir
from .cfg import ApiType

here = os.path.abspath(os.path.dirname(__file__))


_timestamp_re = re.compile(r't": [0-9]+.[0-9]+')


with open(jp(here, "json_test_compact.json")) as _jf:
    _compact_json = _jf.read().strip()


with open(jp(here, "json_test_pretty.json")) as _jf:
    _pretty_json = _jf.read().strip()


def _assert_json(got_json, expected_json, api_type):
    got_json = utils.replace_host_port(api_type, got_json)
    got_json = _timestamp_re.sub(r't": 12345.123', got_json)

    if api_type == ApiType.SCRIPT:
        expected_json = utils.replace_host_port(api_type, expected_json)

    if got_json.strip() != expected_json:
        if not os.environ.get('JOB_NAME'):
            print("--- expected json ---")
            print(expected_json)
            print("--- got json ---")
            print(got_json)
        assert got_json.strip() == expected_json
            

def _flow(api, strip_prefix, json_dir):
    if not os.path.exists(json_dir):
        os.makedirs(json_dir)

    with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=1, json_dir=json_dir, json_strip_top_level_prefix=strip_prefix) as ctrl1:
        ctrl1.invoke('j1')
        ctrl1.invoke('j2')

        with ctrl1.parallel(timeout=40, report_interval=3) as ctrl2:
            with ctrl2.serial(timeout=40, report_interval=3) as ctrl3a:
                ctrl3a.invoke('j3')
                ctrl3a.invoke('j6')
                ctrl3a.invoke_unchecked('j7_unchecked')

            with ctrl2.parallel(timeout=40, report_interval=3) as ctrl3b:
                ctrl3b.invoke('j4')
                ctrl3b.invoke('j5')
                ctrl3b.invoke_unchecked('j8_unchecked')

        ctrl1.invoke('j9')

    return ctrl1


def test_json_strip_prefix(api_type):
    with api_select.api(__file__, api_type, login=True) as api:
        flow_name = api.flow_job()
        api.job('j1', max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j2', max_fails=0, expect_invocations=1, expect_order=2)
        api.job('j3', max_fails=0, expect_invocations=1, expect_order=3)
        api.job('j4', max_fails=0, expect_invocations=1, expect_order=3)
        api.job('j5', max_fails=0, expect_invocations=1, expect_order=3)
        api.job('j6', max_fails=0, expect_invocations=1, expect_order=3)
        api.job('j7_unchecked', max_fails=0, expect_invocations=1, invocation_delay=0, exec_time=40, expect_order=None, unknown_result=True)
        api.job('j8_unchecked', max_fails=0, expect_invocations=1, invocation_delay=0, exec_time=40, expect_order=None, unknown_result=True)
        api.job('j9', max_fails=0, expect_invocations=1, expect_order=4, exec_time=5)

        ctrl1 = _flow(api, True, flow_graph_dir(flow_name))

        # Test pretty printing
        json_file = jp(flow_graph_dir(flow_name), "pretty.json")
        ctrl1.json(json_file, indent=4)
        with open(json_file) as jf:
            _assert_json(jf.read().strip(), _pretty_json, api.api_type)

        # Test default compact json
        with open(ctrl1.json_file) as jf:
            _assert_json(jf.read().strip(), _compact_json, api.api_type)

        # Test return json
        json = ctrl1.json(None)
        _assert_json(json, _compact_json, api.api_type)


def test_json_no_strip_prefix(api_type):
    with api_select.api(__file__, api_type, login=True) as api:
        flow_name = api.flow_job()
        api.job('j1', max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j2', max_fails=0, expect_invocations=1, expect_order=2)
        api.job('j3', max_fails=0, expect_invocations=1, expect_order=3)
        api.job('j4', max_fails=0, expect_invocations=1, expect_order=3)
        api.job('j5', max_fails=0, expect_invocations=1, expect_order=3)
        api.job('j6', max_fails=0, expect_invocations=1, expect_order=3)
        api.job('j7_unchecked', max_fails=0, expect_invocations=1, invocation_delay=0, exec_time=40, expect_order=None, unknown_result=True)
        api.job('j8_unchecked', max_fails=0, expect_invocations=1, invocation_delay=0, exec_time=40, expect_order=None, unknown_result=True)
        api.job('j9', max_fails=0, expect_invocations=1, expect_order=4, exec_time=5)

        ctrl1 = _flow(api, False, flow_graph_dir(flow_name))

        # Test pretty printing with no stripping of top level prefix
        json_file = jp(flow_graph_dir(flow_name), "verbose_pretty.json")
        ctrl1.json(json_file, indent=4)
        with open(json_file) as jf:
            got_json = jf.read().strip()
            expect_json = _pretty_json.replace('strip_prefix', 'no_strip_prefix').replace('name": "', 'name": "jenkinsflow_test__json_no_strip_prefix__')
            _assert_json(got_json, expect_json, api.api_type)


def test_json_unchecked_only_in_flows(api_type):
    with api_select.api(__file__, api_type, login=True) as api:
        flow_name = api.flow_job()
        api.job('j1_unchecked', max_fails=0, expect_invocations=1, invocation_delay=0, exec_time=40, expect_order=None, unknown_result=True)
        api.job('j2_unchecked', max_fails=0, expect_invocations=1, expect_order=None)
        api.job('j3_unchecked', max_fails=0, expect_invocations=1, invocation_delay=0, exec_time=40, expect_order=None, unknown_result=True)
        api.job('j4_unchecked', max_fails=0, expect_invocations=1, invocation_delay=0, exec_time=40, expect_order=None, unknown_result=True)
        api.job('j5_unchecked', max_fails=0, expect_invocations=1, expect_order=None)
        api.job('j6', max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j7', max_fails=0, expect_invocations=1, expect_order=2, exec_time=5)

        json_dir = flow_graph_dir(flow_name)
        if not os.path.exists(json_dir):
            os.makedirs(json_dir)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=1, json_dir=json_dir) as ctrl1:
            ctrl1.invoke_unchecked('j1_unchecked')

            with ctrl1.parallel(timeout=40, report_interval=3) as ctrl2:
                with ctrl2.serial(timeout=40, report_interval=3) as ctrl3a:
                    ctrl3a.invoke_unchecked('j2_unchecked')
                    ctrl3a.invoke_unchecked('j3_unchecked')

                with ctrl2.parallel(timeout=40, report_interval=3) as ctrl3b:
                    ctrl3b.invoke_unchecked('j4_unchecked')
                    ctrl3b.invoke_unchecked('j5_unchecked')

            ctrl1.invoke('j6')
            ctrl1.invoke('j7')

        # Test default compact json
        with open(ctrl1.json_file) as got_jf, open(jp(here, "json_test_unchecked_compact.json")) as expected_jf:
            _assert_json(got_jf.read().strip(), expected_jf.read().strip(), api.api_type)
