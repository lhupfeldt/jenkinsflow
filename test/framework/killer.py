# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import sys, os, signal, time
import subprocess

from jenkinsflow.test.framework.logger import log, logt


def _killer(log_file, pid, sleep_time, num_kills):
    log(log_file, '\n')
    logt(log_file, "Killer going to sleep for", sleep_time, "seconds")
    time.sleep(sleep_time)
    logt(log_file, "Killer woke up")
    for ii in range(0, num_kills):
        logt(log_file, "Killer sending", ii + 1, "of", num_kills, "SIGTERM signals to ", pid)
        os.kill(pid, signal.SIGTERM)
        logt(log_file, "Killer sent", ii + 1, "of", num_kills, "SIGTERM signals to ", pid)
        time.sleep(1)


if __name__ == '__main__':
    log_file_name = sys.argv[4]
    with open(log_file_name, 'a+') as log_file:
        _killer(log_file, int(sys.argv[1]), float(sys.argv[2]), int(sys.argv[3]))


def kill(api, sleep_time, num_kills):
    """Kill this process"""
    pid = os.getpid()    
    ff = __file__.replace('.pyc', '.py')
    log_file_name = api.func_name.replace('test_', '')
    args = [sys.executable, ff, repr(pid), repr(sleep_time), repr(num_kills), log_file_name]
    with open(log_file_name, 'w') as log_file:
        logt(log_file, "Invoking kill subprocess.", args)

    subprocess.Popen(args)
