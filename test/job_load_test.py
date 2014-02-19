#!/usr/bin/python

# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import os
from os.path import join as jp

from jenkinsflow import jobload
from framework import mock_api


here = os.path.abspath(os.path.dirname(__file__))


def test_job_load_pre_delete():
    api = mock_api.api(__file__)
    api.job('loaded', exec_time=0.5, max_fails=1, expect_invocations=1, expect_order=1)
    job_xml_template = jp(here, 'framework/job.xml.tenjin')
    context = dict(exec_time=1, params=(), script=None, securitytoken='abc')
    jobload.update_job_from_template(api, api.job_name_prefix + 'loaded', job_xml_template, pre_delete=True, context=context)


def test_job_load_new():
    api = mock_api.api(__file__)
    job_xml_template = jp(here, 'framework/job.xml.tenjin')
    context = dict(exec_time=1, params=(), script='echo Hello', securitytoken='abc')
    jobload.update_job_from_template(api, api.job_name_prefix + 'loaded', job_xml_template, pre_delete=False, context=context)
