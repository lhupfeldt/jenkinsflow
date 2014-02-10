#!/usr/bin/python

# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

import sys
import os.path
from os.path import join as jp
here = os.path.dirname(__file__)
sys.path.append(jp(here, '../..'))

import logging

from jenkinsflow.jobcontrol import serial
from jenkinsflow.unbuffered import UnBuffered

from framework import mock_api

# Unbuffered output does not work well in Jenkins, so in case
# this is run from a hudson job, we want unbuffered output
sys.stdout = UnBuffered(sys.stdout)

def main():
    logging.basicConfig()
    logging.getLogger("").setLevel(logging.WARNING)

    with mock_api.api(job_name_prefix='no_args_') as api:
        api.mock_job('job-1', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=1)
        print()

        with serial(api, timeout=70, job_name_prefix='no_args_', report_interval=1) as ctrl1:
            ctrl1.invoke('job-1')

if __name__ == '__main__':
    main()
