#!/usr/bin/env python

# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# Deprecated - Compatibility script

from __future__ import print_function
import sys, os


# Deprecated Compatibility - Allow relative imports while running as script. Necessary for testing without installing
if __package__ is None:
    _here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(1, os.path.dirname(_here))
    import jenkinsflow
    __package__ = "jenkinsflow"


def main(args):
    import subprocess32
    _here = os.path.dirname(os.path.abspath(__file__))
    return subprocess32.call([sys.executable, os.path.join(_here, 'cli/cli.py'), 'set_build_description'] + args)


# Deprecated - Compatibility
if __name__ == "__main__":
    main(sys.argv[1:])
