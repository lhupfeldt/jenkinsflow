# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import time

import pytest

from jenkinsflow.speed import Speed

from .framework.cfg import ApiType


@pytest.mark.not_apis(ApiType.MOCK)
def test_hyperspeed_speedup(api_type):
    hs = Speed()
    assert hs.speedup == 1


@pytest.mark.not_apis(ApiType.MOCK)
def test_hyperspeed_real_time(api_type):
    hs = Speed()
    assert hs.time() <= time.time()


@pytest.mark.not_apis(ApiType.MOCK)
def test_hyperspeed_real_sleep(api_type):
    hs = Speed()
    before = time.time()
    hs.sleep(1)
    after = time.time()
    assert after - before >= 1
