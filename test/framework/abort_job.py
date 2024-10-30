# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import sys
import time
import subprocess
from pathlib import Path

from . import api_select
from .logger import log, logt
from .cfg import ApiType, AllCfg, opt_strs_to_test_cfg, test_cfg_to_opt_strs


def _abort(log_file, test_file_name, api_type, fixed_prefix, job_name, sleep_time, test_cfg: AllCfg):
    log(log_file, '\n')
    logt(log_file, "Subprocess", __file__)
    logt(log_file, f"Waiting {sleep_time} seconds to abort job:", job_name)
    logt(log_file, "args:", test_file_name, api_type, fixed_prefix, job_name, sleep_time, test_cfg)
    time.sleep(sleep_time)
    logt(log_file, "sleep", sleep_time, "finished")
    with api_select.api(test_file_name, api_type, fixed_prefix='jenkinsflow_test__' + fixed_prefix + '__', login=True, options=test_cfg) as api:
        api.job(job_name, max_fails=0, expect_invocations=0, expect_order=None)
    logt(log_file, "job defined", api)
    api.poll()
    logt(log_file, "polled")
    api.quick_poll()
    logt(log_file, "quick polled")

    abort_me = api.get_job(api.job_name_prefix + job_name)
    logt(log_file, "Abort job:", abort_me)
    abort_me.stop_all()
    logt(log_file, "Aborted")


if __name__ == '__main__':
    job_name = sys.argv[4]
    with open(job_name + '.log', 'a+', encoding="utf-8") as log_file:
        try:
            _abort(
                log_file, sys.argv[1], ApiType[sys.argv[2]], sys.argv[3], job_name, int(sys.argv[5]),
                test_cfg = opt_strs_to_test_cfg(
                    direct_url=sys.argv[6], load_jobs=sys.argv[7], delete_jobs=sys.argv[8], mock_speedup=sys.argv[9], apis_str=sys.argv[10]))
        except Exception as ex:
            print(ex, file=log_file)
            raise


def abort(api, job_name, sleep_time, test_cfg: AllCfg):
    """Call this script as a subprocess"""
    if api.api_type == ApiType.MOCK:
        return

    args = [sys.executable, "-m", f"jenkinsflow.test.framework.{Path(__file__).stem}",
            api.file_name, api.api_type.name, api.func_name.replace('test_', ''), job_name, str(sleep_time),
            *test_cfg_to_opt_strs(test_cfg, api.api_type)]
    with open(job_name + '.log', 'w', encoding="utf-8") as log_file:
        logt(log_file, "Current dir:", Path.cwd())
        logt(log_file, "Invoking abort subprocess.", args)
    subprocess.Popen(args, start_new_session=True)
