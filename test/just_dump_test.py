# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import os
from os.path import join as jp
from jenkinsflow.flow import serial
from .framework import api_select
from .framework.utils import flow_graph_dir

from .json_test import _assert_json

here = os.path.abspath(os.path.dirname(__file__))


with open(jp(here, "just_dump_test_compact.json")) as _jf:
    _compact_json = _jf.read().strip()


def _flow(api, json_dir):
    if json_dir and not os.path.exists(json_dir):
        os.makedirs(json_dir)

    with serial(api, timeout=1, job_name_prefix=api.job_name_prefix, json_dir=json_dir, json_strip_top_level_prefix=True, just_dump=True) as ctrl1:
        ctrl1.invoke('j1')

        with ctrl1.parallel(timeout=40, report_interval=3) as ctrl2:
            with ctrl2.serial(timeout=40, report_interval=3) as ctrl3a:
                ctrl3a.invoke('j2')
                ctrl3a.invoke_unchecked('j3_unchecked')

            with ctrl2.parallel(timeout=40, report_interval=3) as ctrl3b:
                ctrl3b.invoke('j4')

        ctrl1.invoke('j5')

    return ctrl1


def test_just_dump_no_json():
    with api_select.api(__file__, login=True) as api:
        api.flow_job()
        api.job('j1', exec_time=0.01, max_fails=0, expect_invocations=0, expect_order=None)
        api.job('j2', exec_time=0.01, max_fails=0, expect_invocations=0, expect_order=None)
        api.job('j3_unchecked', exec_time=40, max_fails=0, expect_invocations=0, expect_order=None)
        api.job('j4', exec_time=5, max_fails=0, expect_invocations=0, expect_order=None)
        api.job('j5', exec_time=5, max_fails=0, expect_invocations=0, expect_order=None)

        _flow(api, None)


def test_just_dump_with_json():
    with api_select.api(__file__, login=True) as api:
        flow_name = api.flow_job()
        api.job('j1', exec_time=0.01, max_fails=0, expect_invocations=0, expect_order=None)
        api.job('j2', exec_time=0.01, max_fails=0, expect_invocations=0, expect_order=None)
        api.job('j3_unchecked', exec_time=40, max_fails=0, expect_invocations=0, expect_order=None)
        api.job('j4', exec_time=5, max_fails=0, expect_invocations=0, expect_order=None)
        api.job('j5', exec_time=5, max_fails=0, expect_invocations=0, expect_order=None)

        fgd = flow_graph_dir(flow_name)
        ctrl1 = _flow(api, fgd)

        # Test json
        json = ctrl1.json(None)
        _assert_json(json, _compact_json, api.api_type)
