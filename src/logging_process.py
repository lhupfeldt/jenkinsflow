# Copyright (c) 2012 - 2024 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import sys
import os
import signal
import multiprocessing

import setproctitle


class LoggingProcess(multiprocessing.Process):
    proc_name_prefix = "jenkinsflow_script_api_"

    def __init__(self, group=None, target=None, output_file_name=None, workspace=None, name=None, args=(), env=None):
        self.user_target = target
        super().__init__(group=group, target=self.run_job_wrapper, name=name, args=args)
        self.output_file_name = output_file_name
        self.workspace = workspace
        self.env = env
        self._build_res_unstable = False

    def run_job_wrapper(self, *args):
        setproctitle.setproctitle(self.proc_name_prefix + self.name)

        # Set signalhandler for changing job result
        def set_result(_sig, _frame):
            print("\nGot SIGUSR1: Changing result to 'unstable'")
            self._build_res_unstable = True
        signal.signal(signal.SIGUSR1, set_result)

        os.chdir(self.workspace)
        os.environ.update(self.env)
        os.environ['EXECUTOR_NUMBER'] = repr(self.pid)

        try:
            rc = self.user_target(*args)
        except Exception as ex:  # pylint: disable=broad-except
            print("jenkinsflow.script_api: Caught exception from job script:", ex)
            rc = 1

        if self._build_res_unstable:
            sys.exit(2)
        sys.exit(rc)

    def run(self):
        sys.stdout = sys.stderr = open(self.output_file_name, 'w', buffering=1, encoding="utf-8")
        super().run()
