# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

import sys

from jenkinsflow.mocked import hyperspeed

from jenkinsflow.test.framework import api_select


def abort(test_file_name, fixed_prefix, job_name):
    print("\nWaiting to abort job:", job_name)
    hyperspeed.sleep(2)
    with api_select.api(test_file_name, fixed_prefix='jenkinsflow_test__' + fixed_prefix + '__', login=True) as api:
        api.job(job_name, 0.1, max_fails=0, expect_invocations=0, expect_order=None)
    api.poll()
    api.quick_poll()

    abort_me = api.get_job(api.job_name_prefix + job_name)
    print("Abort job:", abort_me)
    abort_me.stop_all()
    print("Aborted")


abort(sys.argv[1], sys.argv[2], sys.argv[3])
