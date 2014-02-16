#!/usr/bin/python

# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from jenkinsflow.jobcontrol import serial, FailedChildJobException
from framework import mock_api


def main():
    with mock_api.api(__file__) as api:
        api.job('wait2', 2, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('wait5', 5, max_fails=0, expect_invocations=1, expect_order=2)
        api.job('quick_fail', 0.5, max_fails=1, expect_invocations=1, expect_order=2, params=(('s1', 'WORLD', 'desc'), ('c1', ('why', 'not'), 'desc')))
        api.job('not_invoked', 0.5, max_fails=0, expect_invocations=0, expect_order=None)

        try:
            with serial(api, timeout=70, job_name_prefix='multi_level_errors1_', report_interval=3) as ctrl1:
                ctrl1.invoke('wait2')

                with ctrl1.parallel(timeout=20, report_interval=3) as ctrl2:
                    ctrl2.invoke('wait5')
                    ctrl2.invoke('quick_fail', password='Y', fail='yes', s1='WORLD', c1='why')

                # Never invoked because of failure in preceding 'parallel'
                ctrl1.invoke('not_invoked')

            raise Exception("Should have failed!")
        except FailedChildJobException as ex:
            print("Ok, got exception:", ex)
