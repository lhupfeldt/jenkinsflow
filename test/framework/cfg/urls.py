import os, socket

from . import dirs
from . import ApiType


class Urls():
    default_direct_url = "http://localhost:8080"
    proxied_public_url = "http://myproxy.mydom/jenkins"
    _cli_jar_path = 'jnlpJars/jenkins-cli.jar'

    def __init__(self, direct_url, script_dir):
        self._direct_url = direct_url.rstrip('/') if direct_url else self.default_direct_url
        self._script_dir = script_dir.rstrip('/') if script_dir else dirs.job_script_dir

    def direct_url(self, api_type):
        if api_type == ApiType.SCRIPT:
            return self._script_dir

        return self._direct_url

    def public_url(self, api_type):
        if api_type == ApiType.SCRIPT:
            return self._script_dir

        purl = os.environ.get('JENKINS_URL')
        return "http://" + socket.getfqdn() + ':' + repr(8080) + '/' if purl is None else purl

    def direct_cli_url(self, api_type):
        if api_type == ApiType.SCRIPT:
            return self._script_dir

        return self.direct_url(api_type) + '/' + self._cli_jar_path

    def public_cli_url(self, api_type):
        if api_type == ApiType.SCRIPT:
            return self._script_dir

        return self.public_url(api_type) + self._cli_jar_path

    def proxied_public_cli_url(self, api_type):
        # Not required to be a real url
        if api_type == ApiType.SCRIPT:
            return self._script_dir

        return self.proxied_public_url + '/' + self._cli_jar_path
