# Copyright (c) 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from pathlib import Path
import multiprocessing
import time

import bottle
import requests
import pytest
from pytest import raises

from jenkinsflow import jenkins_api

from .framework import api_select
from .framework.utils import lines_in
from .framework.cfg import ApiType


_HERE = Path(__file__).absolute().parent
_STATIC_DIR = _HERE/"framework"


@bottle.route('/')
def _index():
    return bottle.static_file('which_ci_server.html', root=_STATIC_DIR)


@bottle.route('/api/json')
def _api():
    return bottle.static_file('which_ci_server.html', root=_STATIC_DIR)


_host = 'localhost'
_port = 8082


def _server():
    bottle.run(host=_host, port=_port, debug=True)


@pytest.mark.apis(ApiType.JENKINS)
def test_which_ci_server_not_ci(api_type):
    proc = None
    try:
        with api_select.api(__file__, api_type):
            proc = multiprocessing.Process(target=_server)
            proc.start()

            with raises(Exception) as exinfo:
                for _ in range(0, 10):
                    ex = None
                    try:
                        jenkins_api.JenkinsApi("http://" + _host + ':' + repr(_port), "dummy").poll()
                    except requests.exceptions.ConnectionError as ex:
                        # Wait for bottle to start
                        print(ex)
                        time.sleep(0.3)

            assert lines_in(
                api_type, str(exinfo.value),
                 "Not connected to Jenkins. Expected X-Jenkins header, got: "
            )

    finally:
        if proc:
            proc.terminate()
