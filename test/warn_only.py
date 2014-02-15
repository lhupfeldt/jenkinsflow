#!/usr/bin/python

# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

import logging

from jenkinsflow.jobcontrol import serial

from framework import mock_api


def main():
    logging.basicConfig()
    logging.getLogger("").setLevel(logging.WARNING)

    with mock_api.api(__file__) as api:
        api.job('a1', exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=1)
        api.job('a2_fail', exec_time=0.5, max_fails=1, expect_invocations=1, expect_order=2)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=3, warn_only=True) as ctrl1:
            ctrl1.invoke('a1')
            ctrl1.invoke('a2_fail', fail='yes')


if __name__ == '__main__':
    main()
