#!/usr/bin/python

# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import os
from os.path import join as jp
from jenkinsflow.flow import serial
from jenkinsflow.test.framework import mock_api, utils

here = os.path.abspath(os.path.dirname(__file__))

_flow_graph_root_dir = '/tmp/jenkinsflowgraphs'


with open(jp(here, "json_test_compact.json")) as _jf:
    _compact_json = _jf.read().strip()


with open(jp(here, "json_test_pretty.json")) as _jf:
    _pretty_json = _jf.read().strip()


def _assert_json(got_json, expected_json):
    print("--- expected json ---")
    print(expected_json)
    print("--- got json ---")
    got_json = utils.replace_host_port(got_json)
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

            with ctrl2.parallel(timeout=40, report_interval=3) as ctrl3b:
                ctrl3b.invoke('j4')
                ctrl3b.invoke('j5')

        ctrl1.invoke('j7')

    return ctrl1


def test_json_strip_prefix():
    with mock_api.api(__file__) as api:
        flow_name = api.flow_job()
        api.job('j1', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j2', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=2)
        api.job('j3', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=3)
        api.job('j4', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=3)
        api.job('j5', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=3)
        api.job('j6', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=4)
        api.job('j7', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=5)

        ctrl1 = _flow(api, True, jp(_flow_graph_root_dir, flow_name))

        # Test pretty printing
        json_file = jp(_flow_graph_root_dir, flow_name, "pretty.json")
        ctrl1.json(json_file, indent=4)
        with open(json_file) as jf:
            _assert_json(jf.read().strip(), _pretty_json)

        # Test default compact json
        with open(ctrl1.json_file) as jf:
            _assert_json(jf.read().strip(), _compact_json)

        # Test return json
        json = ctrl1.json(None)
        _assert_json(json, _compact_json)


def test_json_no_strip_prefix():
    with mock_api.api(__file__) as api:
        flow_name = api.flow_job()
        api.job('j1', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j2', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=2)
        api.job('j3', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=3)
        api.job('j4', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=3)
        api.job('j5', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=3)
        api.job('j6', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=4)
        api.job('j7', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=5)

        ctrl1 = _flow(api, False, jp(_flow_graph_root_dir, flow_name))

        # Test pretty printing wi no stripping of top level prefix
        json_file = jp(_flow_graph_root_dir, flow_name, "verbose_pretty.json")
        ctrl1.json(json_file, indent=4)
        with open(json_file) as jf:
            got_json = jf.read().strip()
            expect_json = _pretty_json.replace('strip_prefix', 'no_strip_prefix').replace('name": "', 'name": "jenkinsflow_test__json_no_strip_prefix__')
            _assert_json(got_json, expect_json)
