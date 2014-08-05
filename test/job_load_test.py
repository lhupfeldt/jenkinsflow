# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import os, random

from pytest import raises

from jenkinsflow import jobload
from .framework import api_select
from .cfg import ApiType


here = os.path.abspath(os.path.dirname(__file__))

_context = dict(exec_time=1, params=(), script=None, securitytoken='abc', print_env=False, create_job=None)


def _random_job_name(api, short_name=None):
    # If short_name is not specified, use a random name to make sure the job doesn't exist
    short_name = short_name or str(random.random()).replace('.', '')
    return api.job_name_prefix + short_name, short_name


def _assert_job(api, job_name, cleanup=False):
    job = api.get_job(job_name)
    assert job is not None
    assert job.name == job_name
    assert job.baseurl is not None and job_name in job.baseurl

    if cleanup:
        api.delete_job(job_name)
        return None

    return job


def test_job_load_new_no_pre_delete():
    api = api_select.api(__file__, login=True)
    full_name, short_name = _random_job_name(api)
    api.job(short_name, 1, 1, 1, 1)
    jobload.update_job_from_template(api, full_name, api.job_xml_template, pre_delete=False, context=_context)
    _assert_job(api, full_name, cleanup=True)


def test_job_load_new_pre_delete():
    api = api_select.api(__file__, login=True)
    full_name, short_name = _random_job_name(api)
    api.job(short_name, 1, 1, 1, 1)
    jobload.update_job_from_template(api, full_name, api.job_xml_template, pre_delete=True, context=_context)
    _assert_job(api, full_name, cleanup=True)


def test_job_load_existing_pre_delete():
    api = api_select.api(__file__, login=True)
    full_name, short_name = _random_job_name(api)
    api.job(short_name, 1, 1, 1, 1)
    jobload.update_job_from_template(api, full_name, api.job_xml_template, pre_delete=True, context=_context)
    _assert_job(api, full_name, cleanup=False)
    jobload.update_job_from_template(api, full_name, api.job_xml_template, pre_delete=True, context=_context)
    _assert_job(api, full_name, cleanup=True)


def test_job_load__existing_update():
    api = api_select.api(__file__, login=True)
    full_name, short_name = _random_job_name(api)
    api.job(short_name, 1, 1, 1, 1)
    jobload.update_job_from_template(api, full_name, api.job_xml_template, pre_delete=True, context=_context)
    _assert_job(api, full_name, cleanup=False)
    jobload.update_job_from_template(api, full_name, api.job_xml_template, pre_delete=False, context=_context)
    _assert_job(api, full_name, cleanup=True)


def test_job_load_non_existing_pre_delete():
    api = api_select.api(__file__, login=True)
    full_name, _ = _random_job_name(api)
    if api.api_type == ApiType.MOCK:
        # TODO: Since the Mock framework is not suited for testing this we just accept the KeyError, it will still test some code that is not otherwise tested
        with raises(KeyError):
            jobload.update_job_from_template(api, full_name, api.job_xml_template, pre_delete=True, context=_context)
    else:
        jobload.update_job_from_template(api, full_name, api.job_xml_template, pre_delete=True, context=_context)

