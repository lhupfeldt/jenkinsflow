#!/usr/bin/python

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import sys
import os.path
from os.path import join as jp
here = os.path.dirname(__file__)
sys.path.append(jp(here, '../test'))

from clean_jobs_state import clean_jobs_state
import mock_api


def main():
    clean_jobs_state()

    with mock_api.api(__file__) as api:
        def job(name, params=None):
            api.mock_job(name, exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=1, job_xml_template=jp(here, '../test/job.xml.tenjin'), params=params)

        job('prepare')
        job('deploy_component1')
        job('deploy_component2')
        job('report', params=(('s1', 'deploy', 'desc'), ('c1', ('complete', 'partial'), 'desc')))
        job('prepare_tests')
        job('test_ui')
        job('test_server_component1')
        job('test_server_component2')
        job('report', params=(('s1', 'tst_regression', 'desc'), ('c1', ('complete', 'partial'), 'desc')))
        job('promote')


if __name__ == '__main__':
    main()
