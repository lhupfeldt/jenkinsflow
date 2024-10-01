# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import importlib.util
import importlib.machinery
from pathlib import Path

import pytest
from pytest import raises

from jenkinsflow.flow import parallel, JobControlFailException

from jenkinsflow.demo import basic, calculated_flow, prefix, hide_password, errors

from .framework import api_select
from .framework.cfg import ApiType


_HERE = Path(__file__).resolve().parent
_DEMO_JOBS_DIR = (_HERE/"../demo/jobs").resolve()


def _load_source(modname, filename):
    # https://docs.python.org/3/whatsnew/3.12.html#imp
    loader = importlib.machinery.SourceFileLoader(modname, filename)
    spec = importlib.util.spec_from_file_location(modname, filename, loader=loader)
    module = importlib.util.module_from_spec(spec)
    # The module is always executed and not cached in sys.modules.
    # Uncomment the following line to cache the module.
    # sys.modules[module.__name__] = module
    loader.exec_module(module)
    return module


def load_demo_jobs(demo, api_type):
    print("\nLoad jobs for demo:", demo.__name__)
    simple_demo_name = demo.__name__.replace("jenkinsflow.", "").replace("demo.", "")
    job_load_module_name = simple_demo_name + '_jobs'
    job_load = _load_source(job_load_module_name, str(_DEMO_JOBS_DIR/(job_load_module_name + '.py')))
    api = job_load.create_jobs(api_type)
    flow_job_name = simple_demo_name + "__0flow"
    return flow_job_name


def _test_demo(demo, api_type):
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
