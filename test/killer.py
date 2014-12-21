#!/usr/bin/env python

from __future__ import print_function

import sys, os, signal, time


def killer(pid, sleep_time, num_kills):
    print("\nKiller going to sleep for", sleep_time, "seconds")
    time.sleep(float(sleep_time))
    print("\nKiller woke up")
    for ii in range(0, int(num_kills)):
        os.kill(int(pid), signal.SIGTERM)
        print("\nKiller sent", ii + 1, "of", num_kills, "SIGTERM signals to ", pid)
        time.sleep(1)


killer(sys.argv[1], sys.argv[2], sys.argv[3])
