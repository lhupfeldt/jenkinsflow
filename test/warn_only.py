#!/usr/bin/python

# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

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

    with mock_api.api(__file__) as api:
        api.mock_job('a1', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=1, job_xml_template=jp(here, '../test/framework/job.xml.tenjin'))
        api.mock_job('a2_fail', exec_time=0.5, max_fails=1, expect_invocations=1, expect_order=2, job_xml_template=jp(here, '../test/framework/job.xml.tenjin'))

        with serial(api, timeout=70, job_name_prefix='warn_only_', report_interval=3, warn_only=True) as ctrl1:
            ctrl1.invoke('a1')
            ctrl1.invoke('a2_fail', fail='yes')


if __name__ == '__main__':
    main()
