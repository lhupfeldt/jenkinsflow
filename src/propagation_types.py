# Copyright (c) 2019 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from .ordered_enum import OrderedEnum


class Propagation(OrderedEnum):
    # pylint: disable=no-init
    NORMAL = 0
    FAILURE_TO_UNSTABLE = 1
    UNCHECKED = 2
