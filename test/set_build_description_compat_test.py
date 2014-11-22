# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import sys, os, subprocess32
from os.path import join as jp

_here = os.path.dirname(os.path.abspath(__file__))


def test_set_build_result_call_script_help(capfd):
    # Invoke this in a subprocess to ensure that calling the script works
    # This will not give coverage as it not not traced through the subprocess call
    rc = subprocess32.call([sys.executable, jp(_here, '..', 'set_build_description.py'), '--help'])
    assert rc == 0

    sout, _ = capfd.readouterr()
    assert '--job-name' in sout
    assert '--build-number' in sout
    assert '--description' in sout
    assert '--direct-url' in sout
    assert '--replace' in sout
    assert '--separator' in sout
    assert '--username' in sout
    assert '--password' in sout
