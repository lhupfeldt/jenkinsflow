# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from ...framework import api_select


def create_jobs(api_type):
    api = api_select.api(__file__, api_type)
    def job(name, expect_order):
        api.job(name, exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=expect_order, params=None)

    api.flow_job()
    job('quick1', 1)
    index = 0
    for index in 1, 2, 3:
        job('x_quick2-' + str(index), 1+index)
    job('quick3', 2+index)
    job('y_z_quick4', 3+index)
    job('y_quick5', 3+index)
    return api


if __name__ == '__main__':
    create_jobs(api_select.ApiType.JENKINS)
