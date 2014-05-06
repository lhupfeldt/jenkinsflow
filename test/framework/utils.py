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
    """Assert that `*expected_lines` occur in order in the lines of `text`.

    Args:
        *expected_lines (str or RegexObject (hasattr `match`)): For each `expected_line` in expected_lines:
            If `expected_line` has a match method it is called and must return True for a line in `text`.
            Otherwise, if the `expected_line` starts with '^', a line in `text` must start with `expected_line[1:]`
            Otherwise `expected line` must simply occur in a line in `text`
    """
    max_index = len(expected_lines) - 1
    index = 0
    for line in text.split('\n'):
        line = replace_host_port(line)
        expected = expected_lines[index]

        if hasattr(expected, 'match'):
            if expected.match(line):
                index += 1
                if index == max_index:
                    return
            continue

        if expected.startswith('^'):
            if line.startswith(expected[1:]):
                index += 1
                if index == max_index:
                    return
            continue

        if expected in line:
            index += 1
            if index == max_index:
                return

    # pylint: disable=no-member
    pytest.fail("The text:\n\n" + repr(expected) + "\n\n    --- NOT FOUND OR OUT OF ORDER IN ---\n\n" + text)


def flow_graph_dir(flow_name):
    """Control which directory to put flow graph in.

    Put the generated graph in the workspace root if running from Jenkins.
    If running from commandline put it under config.flow_graph_root_dir/flow_name

    Return: dir-name
    """
    return '.' if os.environ.get('JOB_NAME') else jp(flow_graph_root_dir, flow_name)
