# Copyright (c) 2012 - 2017 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import sys
import time
import datetime


def log(file, *msg):
    print(*msg)
    sys.stdout.flush()
    print(*msg, file=file)
    file.flush()


def logt(file, *msg):
    now = datetime.datetime.isoformat(datetime.datetime.utcnow())
    log(file, now, *msg)
