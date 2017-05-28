# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from jenkinsflow.flow import serial
from .framework import api_select


def test_boolean_and_int_params(api_type):
    with api_select.api(__file__, api_type) as api:
        api.flow_job()
        api.job('job-1', max_fails=0, expect_invocations=1, expect_order=1, params=(('b1', False, 'boolean'), ('b2', True, 'boolean')))
        api.job('job-2', max_fails=0, expect_invocations=1, expect_order=2, params=(('i1', 1, 'integer'), ('i2', 2, 'integer')), serial=True)

        with serial(api, timeout=50, job_name_prefix=api.job_name_prefix, report_interval=1) as ctrl1:
            ctrl1.invoke('job-1', b1=True, b2=False)
            ctrl1.invoke('job-2', i1=7, i2=0)
