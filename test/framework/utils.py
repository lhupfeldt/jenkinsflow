# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import os, re
from os.path import join as jp
import pytest

from .config import flow_graph_root_dir


_http_re = re.compile(r'https?://.*?/job/')
def replace_host_port(contains_url):
    return _http_re.sub('http://x.x/job/', contains_url)


def assert_lines_in(text, *expected_lines):
    expected = expected_lines  # [replace_host_port(line) for line in expected_lines]
    max_index = len(expected) - 1
    index = 0
    for line in text.split('\n'):
        line = replace_host_port(line)
        if expected[index] in line:
            if index == max_index:
                break
            index += 1
    else:
        pytest.fail(repr(expected[index:]) + "\n    --- NOT FOUND OR OUT OF ORDER IN ---\n" + text)


def flow_graph_dir(flow_name):
    """
    Put the generated graph in the workspace root if running from Jenkins
    If running from commandline put it under config.flow_graph_root_dir/flow_name
    return: dir-name
    """
    return '.' if os.environ.get('JOB_NAME') else jp(flow_graph_root_dir, flow_name)
