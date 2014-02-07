#!/usr/bin/python

# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import sys
import os.path
from os.path import join as jp
here = os.path.dirname(__file__)
sys.path.append(jp(here, '../test'))

from framework import mock_api


def main():
    with mock_api.api(__file__) as api:
        def job(name, params=None):
            api.mock_job(name, exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=1, job_xml_template=jp(here, '../test/framework/job.xml.tenjin'), params=params)

        job('passwd_args', params=(('s1', 'no-secret', 'desc'), ('passwd', 'p2', 'desc'), ('PASS', 'p3', 'desc')))


if __name__ == '__main__':
    main()
