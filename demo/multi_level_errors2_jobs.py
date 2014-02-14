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
            api.job(name, exec_time=0.5, max_fails=0, expect_invocations=1, expect_order=1, params=params)

        job('wait4-1')
        job('wait2')
        job('quick_fail-1', params=(('s1', 'WORLD', 'desc'), ('c1', ('to', 'be', 'or', 'not'), 'desc')))
        job('quick', params=(('s1', 'WORLD', 'desc'), ('c1', ('maybe', 'certain'), 'desc')))
        job('wait5-2a')
        job('wait5-2b')
        job('wait5-2c')
        job('quick_fail-2', params=(('s1', 'WORLD', 'desc'), ('c1', ('maybe', 'certain'), 'desc')))


if __name__ == '__main__':
    main()
