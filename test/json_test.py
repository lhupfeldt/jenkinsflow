#!/usr/bin/python

# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import re
from jenkinsflow.flow import serial
from framework import mock_api

_http_re = re.compile(r'https?://[^/]*/job/')

_compact_json = """
{"nodes": [{"url": "http://x.x/job/jenkinsflow_test__json__j1", "id": 1, "name": "jenkinsflow_test__json__j1"}, {"url": "http://x.x/job/jenkinsflow_test__json__j2", "id": 2, "name": "jenkinsflow_test__json__j2"}, {"url": "http://x.x/job/jenkinsflow_test__json__j3", "id": 5, "name": "jenkinsflow_test__json__j3"}, {"url": "http://x.x/job/jenkinsflow_test__json__j6", "id": 6, "name": "jenkinsflow_test__json__j6"}, {"url": "http://x.x/job/jenkinsflow_test__json__j4", "id": 8, "name": "jenkinsflow_test__json__j4"}, {"url": "http://x.x/job/jenkinsflow_test__json__j5", "id": 9, "name": "jenkinsflow_test__json__j5"}, {"url": "http://x.x/job/jenkinsflow_test__json__j7", "id": 10, "name": "jenkinsflow_test__json__j7"}], "links": [{"source": 1, "target": 2}, {"source": 2, "target": 5}, {"source": 5, "target": 6}, {"source": 2, "target": 8}, {"source": 2, "target": 9}, {"source": 6, "target": 10}]}
""".strip()

_pretty_json = """
{
    "nodes": [
        {
            "url": "http://x.x/job/jenkinsflow_test__json__j1", 
            "id": "jenkinsflow_test__json__j1", 
            "name": "jenkinsflow_test__json__j1"
        }, 
        {
            "url": "http://x.x/job/jenkinsflow_test__json__j2", 
            "id": "jenkinsflow_test__json__j2", 
            "name": "jenkinsflow_test__json__j2"
        }, 
        {
            "url": "http://x.x/job/jenkinsflow_test__json__j3", 
            "id": "jenkinsflow_test__json__j3", 
            "name": "jenkinsflow_test__json__j3"
        }, 
        {
            "url": "http://x.x/job/jenkinsflow_test__json__j6", 
            "id": "jenkinsflow_test__json__j6", 
            "name": "jenkinsflow_test__json__j6"
        }, 
        {
            "url": "http://x.x/job/jenkinsflow_test__json__j4", 
            "id": "jenkinsflow_test__json__j4", 
            "name": "jenkinsflow_test__json__j4"
        }, 
        {
            "url": "http://x.x/job/jenkinsflow_test__json__j5", 
            "id": "jenkinsflow_test__json__j5", 
            "name": "jenkinsflow_test__json__j5"
        }, 
        {
            "url": "http://x.x/job/jenkinsflow_test__json__j7", 
            "id": "jenkinsflow_test__json__j7", 
            "name": "jenkinsflow_test__json__j7"
        }
    ], 
    "links": [
        {
            "source": "jenkinsflow_test__json__j1", 
            "target": "jenkinsflow_test__json__j2"
        }, 
        {
            "source": "jenkinsflow_test__json__j2", 
            "target": "jenkinsflow_test__json__j3"
        }, 
        {
            "source": "jenkinsflow_test__json__j3", 
            "target": "jenkinsflow_test__json__j6"
        }, 
        {
            "source": "jenkinsflow_test__json__j2", 
            "target": "jenkinsflow_test__json__j4"
        }, 
        {
            "source": "jenkinsflow_test__json__j2", 
            "target": "jenkinsflow_test__json__j5"
        }, 
        {
            "source": "jenkinsflow_test__json__j6", 
            "target": "jenkinsflow_test__json__j7"
        }
    ]
}
""".strip()


def assert_json(got_json, expected_json):
    print("--- expected json ---")
    print(expected_json)
    print("--- got json ---")
    got_json = _http_re.sub('http://x.x/job/', got_json)
    print(got_json)
    assert got_json.strip() == expected_json


def test_json():
    with mock_api.api(__file__) as api:
        api.flow_job()
        api.job('j1', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('j2', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=2)
        api.job('j3', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=3)
        api.job('j4', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=3)
        api.job('j5', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=3)
        api.job('j6', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=4)
        api.job('j7', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=5)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=1, json_dir='.') as ctrl1:
            ctrl1.invoke('j1', password='a', s1='b')
            ctrl1.invoke('j2', password='a', s1='b')

            with ctrl1.parallel(timeout=40, report_interval=3) as ctrl2:
                with ctrl2.serial(timeout=40, report_interval=3) as ctrl3a:
                    ctrl3a.invoke('j3', password='a', s1='b')
                    ctrl3a.invoke('j6', password='a', s1='b')

                with ctrl2.parallel(timeout=40, report_interval=3) as ctrl3b:
                    ctrl3b.invoke('j4', password='a', s1='b')
                    ctrl3b.invoke('j5', password='a', s1='b')

            ctrl1.invoke('j7', password='a', s1='b')

        # Test default compact json
        with open(ctrl1.json_file) as jf:
            assert_json(jf.read().strip(), _compact_json)

        # Test pretty printing
        ctrl1.json("pretty.json", indent=4)
        with open("pretty.json") as jf:
            assert_json(jf.read().strip(), _pretty_json)

        # Test return json
        json = ctrl1.json(None)
        assert_json(json, _compact_json)
