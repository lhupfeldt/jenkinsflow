# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from collections import OrderedDict

from framework import mock_api


def create_jobs():
    g1_components = range(1)
    g2_components = range(2)
    g3_components = range(2)
    component_groups = OrderedDict((('g1', g1_components), ('g2', g2_components), ('g3', g3_components)))

    api = mock_api.api(__file__)
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
    create_jobs()
