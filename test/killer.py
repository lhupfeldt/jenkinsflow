#!/usr/bin/env python

from __future__ import print_function

import sys, os, signal, time


def killer(pid, sleep_time):
    print("\nKiller going to sleep for", sleep_time, "seconds")
    time.sleep(float(sleep_time))
    print("\nKiller woke up")
    os.kill(int(pid), signal.SIGTERM)
    print("\nKiller sent signal to ", pid)


killer(sys.argv[1], sys.argv[2])
