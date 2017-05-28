# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from pytest import raises

from jenkinsflow.flow import serial, FailedChildJobException
from .framework import api_select


def test_multi_level_errors(api_type):
    with api_select.api(__file__, api_type) as api:
        api.flow_job()
        api.job('wait2', max_fails=0, expect_invocations=1, expect_order=1, exec_time=2)
        api.job('wait5', max_fails=0, expect_invocations=1, expect_order=2, exec_time=5)
        api.job('quick_fail', max_fails=1, expect_invocations=1, expect_order=2, params=(('s1', 'WORLD', 'desc'), ('c1', ('why', 'not'), 'desc')))
        api.job('not_invoked', max_fails=0, expect_invocations=0, expect_order=None)

        with raises(FailedChildJobException):
            with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=3) as ctrl1:
                ctrl1.invoke('wait2')

                with ctrl1.parallel(timeout=20, report_interval=3) as ctrl2:
                    ctrl2.invoke('wait5')
                    ctrl2.invoke('quick_fail', password='Y', s1='WORLD', c1='why')

                # Never invoked because of failure in preceding 'parallel'
                ctrl1.invoke('not_invoked')
