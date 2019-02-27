# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import codecs, os
from os.path import join as jp

from jenkinsflow.flow import serial

from .framework import api_select
from .cfg import ApiType


_here = os.path.dirname(os.path.abspath(__file__))


from .set_build_description_test import _clear_description


def _verify_description(api, job, build_number, expected):
    if api.api_type == ApiType.MOCK:
        return

    # Read back description and verify
    if api.api_type == ApiType.JENKINS:
        build_url = "/job/" + job.name + '/' + str(build_number)
        dct = api.get_json(build_url, tree="description")
        description = dct['description']

    if api.api_type == ApiType.SCRIPT:
        with codecs.open(jp(job.workspace, 'description.txt'), encoding='utf-8') as ff:
            description = ff.read()

    assert description == expected


def test_set_build_description_unicode_set_build_description_util(api_type):
    with api_select.api(__file__, api_type, login=True) as api:
        api.flow_job()
        job_name = 'job-1'
        api.job(job_name, max_fails=0, expect_invocations=1, expect_order=1)

        # Need to read the build number
        if api.api_type == ApiType.SCRIPT:
            # TODO: This can't be called here for Jenkins API. Why?
            job = api.get_job(api.job_name_prefix + job_name)
            _clear_description(api, job)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=1, description="«©º") as ctrl1:
            ctrl1.invoke(job_name, password='a', s1='b')

        if api.api_type != ApiType.SCRIPT:
            job = api.get_job(api.job_name_prefix + job_name)
        _, _, build_num = job.job_status()

        api.set_build_description(u'ÆØÅ', job_name=job.name, build_number=build_num)
        api.set_build_description(u'æøå', replace=False, job_name=job.name, build_number=build_num)
        _verify_description(api, job, build_num, u'«©º\nÆØÅ\næøå')
        
        api.set_build_description(u'¶¹²', replace=True, job_name=job.name, build_number=build_num)
        api.set_build_description(u'³¼¢', replace=False, separator='#', job_name=job.name, build_number=build_num)
        api.set_build_description(u'¬<>©‘’Nº', separator='!!', job_name=job.name, build_number=build_num)
        _verify_description(api, job, build_num, u'¶¹²#³¼¢!!¬<>©‘’Nº')
