# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import time

import pytest

from ..cfg import ApiType
from .hyperspeed import HyperSpeed


def test_hyperspeed_speedup():
    hs = HyperSpeed(1000)
    assert hs.speedup == 1000


@pytest.mark.apis(ApiType.MOCK)
def test_hyperspeed_mocked_time():
    hs = HyperSpeed(1000)
    time.sleep(0.001)
    assert hs.time() > time.time()


@pytest.mark.apis(ApiType.MOCK)
def test_hyperspeed_mocked_sleep():
    hs = HyperSpeed(1000)
    before = time.time()
    hs.sleep(1)
    after = time.time()
    assert after - before < 1
