# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import imp
from pathlib import Path

import pytest
from pytest import raises

from jenkinsflow.flow import parallel, JobControlFailException

from demo import basic, calculated_flow, prefix, hide_password, errors

from .framework import api_select
from .cfg import ApiType


_HERE = Path(__file__).resolve().parent
_DEMO_JOBS_DIR = (_HERE/"../demo/jobs").resolve()


def load_demo_jobs(demo, api_type):
    print("\nLoad jobs for demo:", demo.__name__)
    job_load_module_name = demo.__name__.replace("demo.", "") + '_jobs'
    job_load = imp.load_source(job_load_module_name, str(_DEMO_JOBS_DIR/(job_load_module_name + '.py')))
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
