# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

import sys, os, imp
from os.path import join as jp
here = os.path.abspath(os.path.dirname(__file__))

extra_sys_path = [os.path.normpath(path) for path in [here, jp(here, '../..'), jp(here, '../demo'), jp(here, '../demo/jobs'), jp(here, '../../jenkinsapi')]]
sys.path = extra_sys_path + sys.path

from pytest import raises

from jenkinsflow.flow import parallel, JobControlFailException
from .framework import api_select, utils
from . import cfg as test_cfg
from .cfg import ApiType

import basic, calculated_flow, prefix, hide_password, errors


def load_demo_jobs(demo):
    print("\nLoad jobs for demo:", demo.__name__)
    job_load_module_name = demo.__name__ + '_jobs'
    job_load = imp.load_source(job_load_module_name, jp(here, '../demo/jobs', job_load_module_name + '.py'))
    api = job_load.create_jobs()
    return api


def test_demos_good():
    # TODO: script api is not configured to run demos
    if test_cfg.selected_api() == ApiType.SCRIPT:
        return

    demos = (basic, calculated_flow, hide_password, prefix)
    for demo in demos:
        load_demo_jobs(demo)

    with api_select.api(__file__, fixed_prefix="jenkinsflow_demo__") as api:
        for demo in demos:
            api.job(demo.__name__ + "__0flow", 0.01, max_fails=0, expect_invocations=1, expect_order=1)

        with parallel(api, timeout=70, job_name_prefix=api.job_name_prefix) as ctrl1:
            for demo in demos:
                ctrl1.invoke(demo.__name__ + "__0flow")


def test_demos_with_errors():
    # TODO
    if test_cfg.selected_api() == ApiType.SCRIPT:
        return

    demos = (errors,)
    for demo in demos:
        load_demo_jobs(demo)

    with api_select.api(__file__, fixed_prefix="jenkinsflow_demo__") as api:
        for demo in demos:
            api.job(demo.__name__ + "__0flow", 0.01, max_fails=1, expect_invocations=1, expect_order=1)

        with raises(JobControlFailException):
            with parallel(api, timeout=70, job_name_prefix=api.job_name_prefix) as ctrl1:
                for demo in demos:
                    ctrl1.invoke(demo.__name__ + "__0flow")
