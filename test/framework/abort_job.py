# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import sys
import time
import subprocess

from jenkinsflow.test.cfg import ApiType
from jenkinsflow.test.framework import api_select
from jenkinsflow.test.framework.logger import log, logt


def _abort(log_file, test_file_name, api_type, fixed_prefix, job_name, sleep_time):
    log(log_file, '\n')
    logt(log_file, "Waiting to abort job:", job_name)
    logt(log_file, "args:", test_file_name, fixed_prefix, job_name, sleep_time)
    time.sleep(sleep_time)
    with api_select.api(test_file_name, api_type, fixed_prefix='jenkinsflow_test__' + fixed_prefix + '__', login=True) as api:
        api.job(job_name, max_fails=0, expect_invocations=0, expect_order=None)
    api.poll()
    api.quick_poll()

    abort_me = api.get_job(api.job_name_prefix + job_name)
    logt(log_file, "Abort job:", abort_me)
    abort_me.stop_all()
    logt(log_file, "Aborted")


if __name__ == '__main__':
    job_name = sys.argv[4]
    with open(job_name, 'a+') as log_file:
        _abort(log_file, sys.argv[1], ApiType[sys.argv[2]], sys.argv[3], job_name, int(sys.argv[5]))


def abort(api, job_name, sleep_time):
    """Call this script as a subprocess"""
    if api.api_type == ApiType.MOCK:
        return

    ff = __file__.replace('.pyc', '.py')
    args = [sys.executable, ff, api.file_name, api.api_type.name, api.func_name.replace('test_', ''), job_name, str(sleep_time)]
    with open(job_name, 'w') as log_file:
        logt(log_file, "Invoking abort subprocess.", args)
    subprocess.Popen(args)
