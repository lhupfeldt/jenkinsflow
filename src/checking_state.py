# Copyright (c) 2019 - 2024 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from .ordered_enum import OrderedEnum


class Checking(OrderedEnum):
    MUST_CHECK = 0
    HAS_UNCHECKED = 1
    FINISHED = 2
