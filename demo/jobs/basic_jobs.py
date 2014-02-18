#!/usr/bin/python

# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from framework import mock_api


def create_jobs():
    components = range(4)
    api = mock_api.api(__file__)
    def job(name, expect_order, params=None):
        api.job(name, exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=expect_order, params=params)

    api.flow_job()
    job('prepare', 1)
    for component in components:
        job('deploy_component' + str(component), 2)
    job('prepare_tests', 3)
    job('test_ui', 4)
    job('test_x', 4)
    for component in components:
        job('test_server_component' + str(component), 5)
    job('report', 6, params=(('s1', 'tst_regression', 'desc'), ('c1', ('complete', 'partial'), 'desc')))
    job('promote', 7)
    return api


if __name__ == '__main__':
    create_jobs()
