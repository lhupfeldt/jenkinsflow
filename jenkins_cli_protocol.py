# Copyright (c) 2012 - 2017 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.


from enum import Enum


class CliProtocol(Enum):
    http = 0
    ssh = 1
    remoting = 2
