# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from ...framework import api_select


def create_jobs(api_type):
    api = api_select.api(__file__, api_type)
    def job(name, expect_order, params=None):
        api.job(name, exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=expect_order, params=params)

    api.flow_job()
    job('prepare', 1)
    job('deploy_component', 2)
    job('report_deploy', 3)
    job('prepare_tests', 3)
    job('test_x', 4)
    job('test_y', 4)
    job('report', 6, params=(('s1', 'tst_regression', 'desc'), ('c1', ('complete', 'partial'), 'desc')))
    return api


if __name__ == '__main__':
    create_jobs(api_select.ApiType.JENKINS)
