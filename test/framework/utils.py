import re

_http_re = re.compile(r'https?://[^/]*/')
def replace_host_port(contains_url):
    return _http_re.sub('http://x.x/', contains_url)
