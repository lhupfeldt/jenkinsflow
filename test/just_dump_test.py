# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
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


def test_just_dump_no_json(api_type):
    with api_select.api(__file__, api_type, login=True) as api:
        api.flow_job()
        api.job('j1', max_fails=0, expect_invocations=0, expect_order=None)
        api.job('j2', max_fails=0, expect_invocations=0, expect_order=None)
        api.job('j3_unchecked', max_fails=0, expect_invocations=0, expect_order=None, exec_time=40)
        api.job('j4', max_fails=0, expect_invocations=0, expect_order=None, exec_time=5)
        api.job('j5', max_fails=0, expect_invocations=0, expect_order=None, exec_time=5)

        _flow(api, None)


def test_just_dump_with_json(api_type):
    with api_select.api(__file__, api_type, login=True) as api:
        flow_name = api.flow_job()
        api.job('j1', max_fails=0, expect_invocations=0, expect_order=None)
        api.job('j2', max_fails=0, expect_invocations=0, expect_order=None)
        api.job('j3_unchecked', max_fails=0, expect_invocations=0, expect_order=None, exec_time=40)
        api.job('j4', max_fails=0, expect_invocations=0, expect_order=None, exec_time=5)
        api.job('j5', max_fails=0, expect_invocations=0, expect_order=None, exec_time=5)

        fgd = flow_graph_dir(flow_name)
        ctrl1 = _flow(api, fgd)

        # Test json
        json = ctrl1.json(None)
        _assert_json(json, _compact_json, api.api_type)
