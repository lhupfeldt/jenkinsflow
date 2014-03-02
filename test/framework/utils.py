# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import os, re
from os.path import join as jp

from .config import flow_graph_root_dir


_http_re = re.compile(r'https?://[^/]*/')
def replace_host_port(contains_url):
    return _http_re.sub('http://x.x/', contains_url)


def flow_graph_dir(flow_name):
    """
    Put the generated graph in the workspace root if running from Jenkins
    If running from commandline put it under config.flow_graph_root_dir/flow_name
    return: dir-name
    """
    return '.' if os.environ.get('JOB_NAME') else jp(flow_graph_root_dir, flow_name)
