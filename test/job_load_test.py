# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import os, random
from os.path import join as jp

from pytest import raises

from jenkinsflow import jobload
from .framework import mock_api


here = os.path.abspath(os.path.dirname(__file__))

_context = dict(exec_time=1, params=(), script=None, securitytoken='abc')
_job_xml_template = jp(here, 'framework/job.xml.tenjin')


def _random_job_name(api, short_name=None):
    # If short_name is not specified, use a random name to make sure the job doesn't exist
    short_name = short_name or str(random.random())
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
    api = mock_api.api(__file__, login=True)
    full_name, short_name = _random_job_name(api)
    api.job(short_name, 1, 1, 1, 1)
    jobload.update_job_from_template(api, full_name, _job_xml_template, pre_delete=False, context=_context)
    _assert_job(api, full_name, cleanup=True)


def test_job_load_new_pre_delete():
    api = mock_api.api(__file__, login=True)
    full_name, short_name = _random_job_name(api)
    api.job(short_name, 1, 1, 1, 1)
    jobload.update_job_from_template(api, full_name, _job_xml_template, pre_delete=True, context=_context)
    _assert_job(api, full_name, cleanup=True)


def test_job_load_existing_pre_delete():
    api = mock_api.api(__file__, login=True)
    full_name, short_name = _random_job_name(api)
    api.job(short_name, 1, 1, 1, 1)
    jobload.update_job_from_template(api, full_name, _job_xml_template, pre_delete=True, context=_context)
    _assert_job(api, full_name, cleanup=False)
    jobload.update_job_from_template(api, full_name, _job_xml_template, pre_delete=True, context=_context)
    _assert_job(api, full_name, cleanup=True)


def test_job_load__existing_update():
    api = mock_api.api(__file__, login=True)
    full_name, short_name = _random_job_name(api)
    api.job(short_name, 1, 1, 1, 1)
    jobload.update_job_from_template(api, full_name, _job_xml_template, pre_delete=True, context=_context)
    _assert_job(api, full_name, cleanup=False)
    jobload.update_job_from_template(api, full_name, _job_xml_template, pre_delete=False, context=_context)
    _assert_job(api, full_name, cleanup=True)


def test_job_load_non_existing_pre_delete():
    api = mock_api.api(__file__, login=True)
    full_name, _ = _random_job_name(api)
    if api.is_mocked:
        # TODO: Since the Mock framework is not suited for testing this we just accept the KeyError, it will still test some code that is not otherwise tested
        with raises(KeyError):
            jobload.update_job_from_template(api, full_name, _job_xml_template, pre_delete=True, context=_context)
    else:
        jobload.update_job_from_template(api, full_name, _job_xml_template, pre_delete=True, context=_context)

