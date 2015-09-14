# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import time

import pytest

from jenkinsflow import hyperspeed

from .cfg import ApiType


def test_hyperspeed_speedup():
    assert hyperspeed.mocked() in (True, False)
    assert isinstance(hyperspeed.get_speedup(), (int, float))


@pytest.mark.apis(ApiType.MOCK)
def test_hyperspeed_mocked_time():
    time.sleep(0.01)
    assert hyperspeed.time() > time.time()


@pytest.mark.apis(ApiType.MOCK)
def test_hyperspeed_mocked_sleep():
    before = time.time()
    hyperspeed.sleep(1)
    after = time.time()
    assert after - before < 1


@pytest.mark.not_apis(ApiType.MOCK)
def test_hyperspeed_real_time():
    time.sleep(0.01)
    assert hyperspeed.time() <= time.time()


@pytest.mark.not_apis(ApiType.MOCK)
def test_hyperspeed_real_sleep():
    before = time.time()
    hyperspeed.sleep(1)
    after = time.time()
    assert after - before >= 1
