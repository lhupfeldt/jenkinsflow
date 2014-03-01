# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import re

_http_re = re.compile(r'https?://[^/]*/')
def replace_host_port(contains_url):
    return _http_re.sub('http://x.x/', contains_url)
