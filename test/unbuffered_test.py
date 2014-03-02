#!/usr/bin/python

# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import sys

from framework import mock_api
from jenkinsflow.flow import serial
from jenkinsflow.unbuffered import UnBuffered


def test_unbuffered():
    sys.stdout = UnBuffered(sys.stdout)
    with mock_api.api(__file__) as api:
        api.flow_job()
        api.job('unbuf', exec_time=0.01, max_fails=0, expect_invocations=1, expect_order=1)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix) as ctrl:
            ctrl.invoke('unbuf')

    assert sys.stdout.writable() == True
