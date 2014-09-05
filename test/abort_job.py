# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

import time

from jenkinsflow.flow import serial

from jenkinsflow.test.framework import api_select


def abort():
    print("Waiting to abort")
    time.sleep(2)
    with api_select.api("abort_test.py", login=True) as api:
        api.job('wait10_abort', 0.1, max_fails=0, expect_invocations=0, expect_order=None)
    api.poll()
    api.quick_poll()

    abort_me = api.get_job(api.job_name_prefix + 'wait10_abort')
    print("abort_me:", abort_me)
    abort_me.stop_all()
    print("Aborted")


abort()
