# Copyright (c) 2012 - 2024 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from ...framework import api_select


def create_jobs(api_type):
    component_groups = {
        'g1': range(1),
        'g2': range(2),
        'g3': range(2),
    }

    api = api_select.api(__file__, api_type)
    def job(name, expect_order, params=None):
        api.job(name, exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=expect_order, params=params)

    api.flow_job()
    job('prepare', 1)
    for gname, group in component_groups.items():
        for component in group:
            job('deploy_component_' + gname + '_' + str(component), 2)
    job('report_deploy', 3)
    job('prepare_tests', 3)
    job('test_ui', 4)
    job('test_x', 4)
    for gname, group in component_groups.items():
        for component in group:
            job('test_component_' + gname + '_' + str(component), 5)
    job('report', 6, params=(('s1', 'tst_regression', 'desc'), ('c1', ('complete', 'partial'), 'desc')))
    job('promote', 7)
    return api


if __name__ == '__main__':
    create_jobs(api_select.ApiType.JENKINS)
