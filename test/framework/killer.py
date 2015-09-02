# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

import sys, os, signal, time, subprocess32

sys.path.append('../../..')
from jenkinsflow.mocked import hyperspeed


def _killer(pid, sleep_time, num_kills):
    print("\nKiller going to sleep for", sleep_time, "seconds")
    time.sleep(sleep_time)
    print("\nKiller woke up")
    for ii in range(0, num_kills):
        os.kill(pid, signal.SIGTERM)
        print("\nKiller sent", ii + 1, "of", num_kills, "SIGTERM signals to ", pid)
        hyperspeed.sleep(1)


if __name__ == '__main__':    
    _killer(int(sys.argv[1]), float(sys.argv[2]), int(sys.argv[3]))


def kill(sleep_time, num_kills):
    """Kill this process"""
    pid = os.getpid()
    print("kill, pid:", pid)
    subprocess32.Popen([sys.executable, __file__, repr(pid), repr(sleep_time), repr(num_kills)])
