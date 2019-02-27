# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import sys, os, imp
from os.path import join as jp
here = os.path.abspath(os.path.dirname(__file__))

extra_sys_path = [os.path.normpath(path) for path in [here, jp(here, '../..'), jp(here, '../demo'), jp(here, '../demo/jobs')]]
sys.path = extra_sys_path + sys.path

import pytest
from pytest import raises

from jenkinsflow.flow import parallel, JobControlFailException
from .framework import api_select
from .cfg import ApiType

import basic, calculated_flow, prefix, hide_password, errors


def load_demo_jobs(demo, api_type):
    print("\nLoad jobs for demo:", demo.__name__)
    job_load_module_name = demo.__name__ + '_jobs'
    job_load = imp.load_source(job_load_module_name, jp(here, '../demo/jobs', job_load_module_name + '.py'))
    api = job_load.create_jobs(api_type)
    return api


def _test_demo(demo, api_type):
    load_demo_jobs(demo, api_type)

    with api_select.api(__file__, api_type, fixed_prefix="jenkinsflow_demo__") as api:
        api.job(demo.__name__ + "__0flow", max_fails=0, expect_invocations=1, expect_order=1)

        with parallel(api, timeout=70, job_name_prefix=api.job_name_prefix) as ctrl1:
            ctrl1.invoke(demo.__name__ + "__0flow")


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
    demo = errors
    load_demo_jobs(demo, api_type)

    with api_select.api(__file__, api_type, fixed_prefix="jenkinsflow_demo__") as api:
        api.job(demo.__name__ + "__0flow", max_fails=1, expect_invocations=1, expect_order=1)

        with raises(JobControlFailException):
            with parallel(api, timeout=70, job_name_prefix=api.job_name_prefix) as ctrl1:
                ctrl1.invoke(demo.__name__ + "__0flow")
