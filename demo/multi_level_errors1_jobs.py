#!/usr/bin/python

# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from framework import mock_api


def main():
    with mock_api.api(__file__) as api:
        def job(name, params=None):
            api.job(name, exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=1, params=params)

        api.flow_job('flow')
        job('wait4-1')
        job('wait5-1')
        job('quick_fail', params=(('s1', 'WORLD', 'desc'), ('c1', ('why', 'not'), 'desc')))
        job('wait4-2')


if __name__ == '__main__':
    main()
