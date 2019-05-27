# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import os, re, tempfile
from os.path import join as jp
from functools import partial

import pytest

from jenkinsflow.test import cfg as test_cfg
from jenkinsflow.test.cfg import ApiType
from .config import flow_graph_root_dir
from .lines_in import lines_in as generic_lines_in


_log_file_prefix = tempfile.gettempdir() + '/jenkinsflow/'


def _script_api_log_file(job_name):
    return _log_file_prefix + job_name + '.log'


def console_url(api, job_name, num):
    if api.api_type == ApiType.SCRIPT:
        return _script_api_log_file(job_name)
    return 'http://x.x/job/' + job_name + '/' + (str(num) + "/console" if api.api_type == ApiType.MOCK else "")


def result_msg(api, job_name, num=None):
    if api.api_type == ApiType.SCRIPT:
        return repr(job_name) + " - build: " + _script_api_log_file(job_name)
    return repr(job_name) + " - build: http://x.x/job/" + job_name + "/" + (str(num) + "/console" if api.api_type == ApiType.MOCK and num else "")


def build_started_msg(api, job_name, num, invocation_number=0):
    return "Build started: " + repr(job_name) + ((' Invocation-' + repr(invocation_number)) if invocation_number else '') + " - " + console_url(api, job_name, num)


def kill_current_msg(api, job_name, num):
    return "Killing build: " + repr(job_name) + " - " + console_url(api, job_name, num)


def build_queued_msg(api, job_name, num):
    if api.api_type == ApiType.MOCK:
        queued_why = r"Why am I queued\?"
    else:
        queued_why = r"Build #[0-9]+ is already in progress \(ETA: ?([0-9.]+ sec|N/A)\)"
    return re.compile("^job: '" + job_name + "' Status QUEUED - " + queued_why)


_http_re = re.compile(r'https?://.*?/job/([^/" ]*)(/?)')
def replace_host_port(api_type, contains_url):
    if api_type != ApiType.SCRIPT:
        return _http_re.sub(r'http://x.x/job/\1\2', contains_url)
    else:
        return _http_re.sub(r'/tmp/jenkinsflow-test/job/\1.py', contains_url)


def lines_in(api_type, text, *expected_lines):
    """Assert that `*expected_lines` occur in order in the lines of `text`.

    Args:
        *expected_lines (str or RegexObject (hasattr `match`)): For each `expected_line` in expected_lines:
            If `expected_line` has a match method it is called and must return True for a line in `text`.
            Otherwise, if the `expected_line` starts with '^', a line in `text` must start with `expected_line[1:]`
            Otherwise `expected line` must simply occur in a line in `text`
    """

    assert isinstance(api_type, test_cfg.ApiType)
    assert text
    assert expected_lines

    return generic_lines_in(text, partial(replace_host_port, api_type), *expected_lines)


def flow_graph_dir(flow_name):
    """Control which directory to put flow graph in.

    Put the generated graph in the workspace root if running from Jenkins.
    If running from commandline put it under config.flow_graph_root_dir/flow_name

    Return: dir-name
    """
    return '.' if os.environ.get('JOB_NAME') else jp(flow_graph_root_dir, flow_name)
