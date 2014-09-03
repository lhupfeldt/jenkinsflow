#!/usr/bin/env python

from __future__ import print_function

import sys, os, signal, time


def killer(pid):
    print("\nKiller going to sleep")
    time.sleep(5)
    print("\nKiller woke up")
    os.kill(int(pid), signal.SIGTERM)
    print("\nKiller sent signal to ", pid)


killer(sys.argv[1])
