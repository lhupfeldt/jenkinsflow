# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from ...framework import api_select


def create_jobs(api_type):
    api = api_select.api(__file__, api_type)
    def job(name, exec_time, max_fails=0, expect_order=0, expect_invocations=1, params=None):
        api.job(name, exec_time=exec_time, max_fails=max_fails, expect_invocations=expect_invocations, expect_order=expect_order, params=params)

    api.flow_job()
    job('wait1-1', 1, 0, 1)
    job('wait2', 2, 0, 2)
    job('wait5-2a', 5, 0, 2)
    job('quick_fail-2', 0.1, 1, 2, params=(('s1', 'WORLD', 'desc'), ('c1', ('maybe', 'certain'), 'desc')))
    job('wait5-2b', 5, 0, 2)
    job('wait5-2c', 5, 0, 2)
    job('quick_fail-1', 0.5, 1, 2, params=(('s1', 'WORLD', 'desc'), ('c1', ('to', 'be', 'or', 'not'), 'desc')))
    job('quick', 0.5, 0, 2, expect_invocations=0, params=(('s1', 'WORLD', 'desc'), ('c1', ('maybe', 'certain'), 'desc')))
    job('wait1-2', 1, 0, 3, expect_invocations=0)
    return api


if __name__ == '__main__':
    create_jobs(api_select.ApiType.JENKINS)
