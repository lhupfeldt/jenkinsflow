# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import sys
import importlib
# import importlib.machinery
from pathlib import Path

import pytest
from pytest import raises

from jenkinsflow.flow import parallel, JobControlFailException

_HERE = Path(__file__).absolute().parent
_DEMO_JOBS_DIR = _HERE/"demos/jobs"

from demo import basic, calculated_flow, prefix, hide_password, errors

from .framework import api_select
from .framework.cfg import ApiType


def load_demo_jobs(demo, api_type):
    print("\nLoad jobs for demo:", demo.__name__)
    simple_demo_name = demo.__name__.replace("demo.", "")
    job_load_module_name = ".demos.jobs." + simple_demo_name + '_jobs'
    job_load = importlib.import_module(job_load_module_name, "test")
    api = job_load.create_jobs(api_type)
    flow_job_name = simple_demo_name + "__0flow"
    return flow_job_name


def _test_demo(demo, api_type):
    print("_test_demo", demo, api_type)
    flow_job_name = load_demo_jobs(demo, api_type)

    with api_select.api(__file__, api_type, fixed_prefix="jenkinsflow_demo__") as api:
        api.job(flow_job_name, max_fails=0, expect_invocations=1, expect_order=1)

        with parallel(api, timeout=70, job_name_prefix=api.job_name_prefix) as ctrl1:
            ctrl1.invoke(flow_job_name)


@pytest.mark.not_apis(ApiType.SCRIPT)  # TODO: script api is not configured to run demos
def test_demos_basic(api_type):
    _test_demo(basic, api_type)


@pytest.mark.not_apis(ApiType.SCRIPT)  # TODO: script api is not configured to run demos
def test_demos_calculated_flow(api_type):
    _test_demo(calculated_flow, api_type)


@pytest.mark.not_apis(ApiType.SCRIPT)  # TODO: script api is not configured to run demos
def test_demos_prefix(api_type):
    _test_demo(prefix, api_type)


@pytest.mark.not_apis(ApiType.SCRIPT)  # TODO: script api is not configured to run demos
def test_demos_hide_password(api_type):
    _test_demo(hide_password, api_type)


@pytest.mark.not_apis(ApiType.SCRIPT)  # TODO: script api is not configured to run demos
def test_demos_with_errors(api_type):
    flow_job_name = load_demo_jobs(errors, api_type)

    with api_select.api(__file__, api_type, fixed_prefix="jenkinsflow_demo__") as api:
        api.job(flow_job_name, max_fails=1, expect_invocations=1, expect_order=1)

        with raises(JobControlFailException):
            with parallel(api, timeout=70, job_name_prefix=api.job_name_prefix) as ctrl1:
                ctrl1.invoke(flow_job_name)
