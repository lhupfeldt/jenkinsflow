# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

import sys
major_version = sys.version_info.major
if major_version < 3:
    import subprocess32 as subprocess
else:
    import subprocess

from jenkinsflow.mocked import hyperspeed

from jenkinsflow.test.framework import api_select
from jenkinsflow.test.cfg import ApiType


def _abort(test_file_name, fixed_prefix, job_name, sleep_time):
    print("\nWaiting to abort job:", job_name)
    print("args:", test_file_name, fixed_prefix, job_name, sleep_time)
    hyperspeed.sleep(sleep_time)
    with api_select.api(test_file_name, fixed_prefix='jenkinsflow_test__' + fixed_prefix + '__', login=True) as api:
        api.job(job_name, 0.1, max_fails=0, expect_invocations=0, expect_order=None)
    api.poll()
    api.quick_poll()

    abort_me = api.get_job(api.job_name_prefix + job_name)
    print("Abort job:", abort_me)
    abort_me.stop_all()
    print("Aborted")


if __name__ == '__main__':    
    _abort(sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]))


def abort(api, job_name, sleep_time):
    """Call this script as a subprocess"""
    if api.api_type != ApiType.MOCK:
        subprocess.Popen([sys.executable, __file__, api.file_name, api.func_name.replace('test_', ''), job_name, str(sleep_time)])
