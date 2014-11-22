# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# NOTE: the tests here all raise exceptions because they can not really be run outside of a jenkinsjob
# TODO: Test that the script actually does what expected! The test here just assure that the script can be run :(

import sys, os, urllib2, re, subprocess32
from os.path import join as jp

from pytest import raises, xfail  # pylint: disable=no-name-in-module

from jenkinsflow import set_build_result
from jenkinsflow.flow import serial, Propagation
from .framework import api_select
from .framework.utils import assert_lines_in
from . import cfg as test_cfg
from .cfg import ApiType

from demo_security import username, password

here = os.path.abspath(os.path.dirname(__file__))

from .set_build_result_test import pre_existing_cli, no_pre_existing_cli


def test_set_build_result_compat_call_main_direct_url_trailing_slash(fake_java, env_base_url):
    with api_select.api(__file__):
        pre_existing_cli()
        base_url = test_cfg.direct_url() + '/'
        set_build_result.main(['--direct-url', base_url])


def test_set_build_result_compat_call_main_direct_url_no_trailing_slash(fake_java, env_base_url):
    with api_select.api(__file__):
        pre_existing_cli()
        base_url = test_cfg.direct_url().rstrip('/')
        set_build_result.main(['--direct-url', base_url])


def test_set_build_result_compat_call_script_help(capfd):
    # Invoke this in a subprocess to ensure that calling the script works
    # This will not give coverage as it not not traced through the subprocess call
    rc = subprocess32.call([sys.executable, jp(here, '..', 'set_build_result.py'), '--help'])
    assert rc == 0

    sout, _ = capfd.readouterr()
    assert '--result' in sout
    assert '--direct-url' in sout
    assert '--username' in sout
    assert '--password' in sout
    assert '--java' in sout
