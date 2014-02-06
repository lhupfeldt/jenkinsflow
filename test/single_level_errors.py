#!/usr/bin/python

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import sys, time
import os.path
from os.path import join as jp
here = os.path.dirname(__file__)
sys.path.append(jp(here, '../..'))

import logging

from jenkinsapi import jenkins

from jenkinsflow.jobcontrol import parallel, serial, FailedChildJobException, FailedChildJobsException, FlowTimeoutException
from jenkinsflow.unbuffered import UnBuffered

from framework import mock_api

sys.stdout = UnBuffered(sys.stdout)

def main():
    logging.basicConfig()
    logging.getLogger("").setLevel(logging.WARNING)
    template = jp(here, './framework/job.xml.tenjin')

    with mock_api.api(job_name_prefix='sle_') as api:
        api.mock_job('quick', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=1, job_xml_template=template, params=(('s1', '', 'desc'), ('c1', 'false', 'desc')))
        api.mock_job('quick_fail', exec_time=0.5, max_fails=1, expect_invocations=1, expect_order=1, job_xml_template=template, params=(('fail', 'true', 'Force job to fail'),))
        api.mock_job('wait10', exec_time=10, max_fails=0, expect_invocations=1, expect_order=1)
        api.mock_job('wait10_fail', exec_time=10, max_fails=1, expect_invocations=1, expect_order=1, job_xml_template=template, params=(('fail', 'true', 'Force job to fail'),))
        api.mock_job('wait5', exec_time=5, max_fails=0, expect_invocations=1, expect_order=1)
        api.mock_job('wait5_fail', exec_time=5, max_fails=1, expect_invocations=1, expect_order=1, job_xml_template=template, params=(('fail', 'true', 'Force job to fail'),))
    
        try:
            with parallel(api, timeout=20, job_name_prefix='sle_', report_interval=3) as ctrl:
                ctrl.invoke('quick', password='Yes', s1='', c1='false')
                ctrl.invoke('quick_fail')
                ctrl.invoke('wait10')
                ctrl.invoke('wait10_fail', fail='yes')
                ctrl.invoke('wait5')
                ctrl.invoke('wait5_fail', fail='yes')
            raise Exception("Should have failed!")
        except FailedChildJobsException as ex:
            print "Ok, got exception:", ex
    
    with mock_api.api(job_name_prefix='sle_') as api:
        api.mock_job('quick', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=1, job_xml_template=template, params=(('s1', '', 'desc'), ('c1', 'false', 'desc')))
        api.mock_job('quick_fail', exec_time=0.5, max_fails=1, expect_invocations=1, expect_order=2, job_xml_template=template, params=(('fail', 'true', 'Force job to fail'),))
        api.mock_job('wait5', exec_time=5, max_fails=0, expect_invocations=0, expect_order=None)

        try:
            with serial(api, timeout=20, job_name_prefix='sle_', report_interval=3) as ctrl:
                ctrl.invoke('quick', password='Yes', s1='', c1='false')
                ctrl.invoke('quick_fail', fail='yes')
                ctrl.invoke('wait5')
            raise Exception("Should have failed!")
        except FailedChildJobException as ex:
            print "Ok, got exception:", ex
    
    with mock_api.api(job_name_prefix='sle_') as api:
        api.mock_job('quick', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=1, job_xml_template=template, params=(('s1', '', 'desc'), ('c1', 'false', 'desc')))
        api.mock_job('wait5', exec_time=5, max_fails=0, expect_invocations=1, expect_order=1)

        try:
            with parallel(api, timeout=1, job_name_prefix='sle_', report_interval=3) as ctrl:
                ctrl.invoke('quick', password='Yes', s1='', c1='false')
                ctrl.invoke('wait5', sleep="5")
            raise Exception("Should have failed!")
        except FlowTimeoutException as ex:
            print "Ok, got exception:", ex
            time.sleep(5)


if __name__ == '__main__':
    main()
