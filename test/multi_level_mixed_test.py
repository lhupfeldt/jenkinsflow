# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from jenkinsflow.flow import serial
from .framework import api_select


def test_multi_level_mixed(api_type):
    with api_select.api(__file__, api_type) as api:
        api.flow_job()
        _params = (('password', '', 'Some password'), ('s1', '', 'Some string argument'))
        api.job('job-1', max_fails=0, expect_invocations=1, expect_order=1, params=_params)
        api.job('job-2', max_fails=0, expect_invocations=1, expect_order=2, params=_params, serial=True)
        api.job('job-3', max_fails=0, expect_invocations=1, expect_order=3, params=_params)
        api.job('job-4', max_fails=0, expect_invocations=1, expect_order=3, params=_params)
        api.job('job-5', max_fails=0, expect_invocations=1, expect_order=3, params=_params)
        api.job('job-6', max_fails=0, expect_invocations=1, expect_order=4, params=_params)
        api.job('job-7', max_fails=0, expect_invocations=1, expect_order=5, params=_params, serial=True)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=1) as ctrl1:
            ctrl1.invoke('job-1', password='a', s1='b')
            ctrl1.invoke('job-2', password='a', s1='b')

            with ctrl1.parallel(timeout=40, report_interval=3) as ctrl2:
                with ctrl2.serial(timeout=40, report_interval=3) as ctrl3a:
                    ctrl3a.invoke('job-3', password='a', s1='b')
                    ctrl3a.invoke('job-6', password='a', s1='b')

                with ctrl2.parallel(timeout=40, report_interval=3) as ctrl3b:
                    ctrl3b.invoke('job-4', password='a', s1='b')
                    ctrl3b.invoke('job-5', password='a', s1='b')

            ctrl1.invoke('job-7', password='a', s1='b')
