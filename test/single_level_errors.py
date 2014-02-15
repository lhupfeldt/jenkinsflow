#!/usr/bin/python

# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

from jenkinsflow.jobcontrol import parallel, serial, FailedChildJobException, FailedChildJobsException, FlowTimeoutException
from framework import mock_api


def main():
    with mock_api.api(job_name_prefix=__file__ + '1') as api:
        api.job('quick', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=1, params=(('s1', '', 'desc'), ('c1', 'false', 'desc')))
        api.job('quick_fail', exec_time=0.5, max_fails=1, expect_invocations=1, expect_order=1, params=(('fail', 'true', 'Force job to fail'),))
        api.job('wait10', exec_time=10, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('wait10_fail', exec_time=10, max_fails=1, expect_invocations=1, expect_order=1, params=(('fail', 'true', 'Force job to fail'),))
        api.job('wait5', exec_time=5, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('wait5_fail', exec_time=5, max_fails=1, expect_invocations=1, expect_order=1, params=(('fail', 'true', 'Force job to fail'),))

        try:
            with parallel(api, timeout=20, job_name_prefix=api.job_name_prefix, report_interval=3) as ctrl:
                ctrl.invoke('quick', password='Yes', s1='', c1=False)
                ctrl.invoke('quick_fail')
                ctrl.invoke('wait10')
                ctrl.invoke('wait10_fail', fail='yes')
                ctrl.invoke('wait5')
                ctrl.invoke('wait5_fail', fail='yes')
            raise Exception("Should have failed!")
        except FailedChildJobsException as ex:
            print("Ok, got exception:", ex)

    with mock_api.api(job_name_prefix=__file__ + '2') as api:
        api.job('quick', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=1, params=(('s1', '', 'desc'), ('c1', 'false', 'desc')))
        api.job('quick_fail', exec_time=0.5, max_fails=1, expect_invocations=1, expect_order=2, params=(('fail', 'true', 'Force job to fail'),))
        api.job('wait5', exec_time=5, max_fails=0, expect_invocations=0, expect_order=None)

        try:
            with serial(api, timeout=20, job_name_prefix=api.job_name_prefix, report_interval=3) as ctrl:
                ctrl.invoke('quick', password='Yes', s1='', c1=False)
                ctrl.invoke('quick_fail', fail='yes')
                ctrl.invoke('wait5')
            raise Exception("Should have failed!")
        except FailedChildJobException as ex:
            print("Ok, got exception:", ex)

    with mock_api.api(job_name_prefix=__file__ + '3') as api:
        api.job('quick', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=1, params=(('s1', '', 'desc'), ('c1', 'false', 'desc')))
        api.job('wait5', exec_time=5, max_fails=0, expect_invocations=1, expect_order=1)

        try:
            with parallel(api, timeout=1, job_name_prefix=api.job_name_prefix, report_interval=3) as ctrl:
                ctrl.invoke('quick', password='Yes', s1='', c1=False)
                ctrl.invoke('wait5', sleep="5")
            raise Exception("Should have failed!")
        except FlowTimeoutException as ex:
            print("Ok, got exception:", ex)


if __name__ == '__main__':
    main()
