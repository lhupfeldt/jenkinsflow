#!/usr/bin/python

# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from jenkinsflow.jobcontrol import parallel, serial
from framework import mock_api


def test_single_level():
    with mock_api.api(__file__ + '1') as api:
        api.job('quick', 0.5, max_fails=0, expect_invocations=1, expect_order=1, params=(('s1', 'Hi', 'desc'), ('c1', ('true', 'maybe', 'false'), 'desc')))
        api.job('wait10', 10, max_fails=0, expect_invocations=1, expect_order=2)
        api.job('wait5', 5, max_fails=0, expect_invocations=1, expect_order=3)

        with serial(api, timeout=40, job_name_prefix=api.job_name_prefix, report_interval=1) as ctrl:
            ctrl.invoke('quick', password='X', s1='HELLO', c1=True)
            ctrl.invoke('wait10')
            ctrl.invoke('wait5')

    with mock_api.api(__file__ + '2') as api:
        api.job('quick', 0.5, max_fails=0, expect_invocations=1, expect_order=1, params=(('s1', 'Hi', 'desc'), ('c1', ('true', 'maybe', 'false'), 'desc')))
        api.job('wait10', 10, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('wait5', 5, max_fails=0, expect_invocations=1, expect_order=1)

        with parallel(api, timeout=20, job_name_prefix=api.job_name_prefix, report_interval=3) as ctrl:
            ctrl.invoke('quick', password='Y', s1='WORLD', c1='maybe')
            ctrl.invoke('wait10')
            ctrl.invoke('wait5')
