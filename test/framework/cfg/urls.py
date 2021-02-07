import os, socket

from . import dirs
from . import ApiType
from .os_env import ENV_VAR_PREFIX


class Urls():
    direct_url_env_var_name = ENV_VAR_PREFIX + 'DIRECT_URL'
    script_dir_env_var_name = ENV_VAR_PREFIX + 'SCRIPT_DIR'

    proxied_public_url = "http://myproxy.mydom/jenkins"

    @staticmethod
    def direct_url(api_type):
        if api_type != ApiType.SCRIPT:
            durl = os.environ.get(Urls.direct_url_env_var_name)
            return 'http://localhost:8080' if durl is None else durl.rstrip('/')
        else:
            return Urls._script_dir()

    @staticmethod
    def public_url(api_type):
        if api_type != ApiType.SCRIPT:
            purl = os.environ.get('JENKINS_URL') or os.environ.get('HUDSON_URL')
            return "http://" + socket.getfqdn() + ':' + repr(8080) + '/' if purl is None else purl
        else:
            return Urls._script_dir()

    @staticmethod
    def direct_cli_url(api_type):
        if api_type != ApiType.SCRIPT:
            purl = os.environ.get('JENKINS_URL')
            if purl:
                return Urls.direct_url(api_type) + '/jnlpJars/jenkins-cli.jar'
            purl = os.environ.get('HUDSON_URL')
            if purl:
                return Urls.direct_url(api_type) + '/jnlpJars/hudson-cli.jar'
            # If neither JENKINS nor HUDSON URL is set, assume jenkins for testing
            return Urls.direct_url(api_type) + '/jnlpJars/jenkins-cli.jar'
        else:
            return Urls._script_dir()

    @staticmethod
    def public_cli_url(api_type):
        if api_type != ApiType.SCRIPT:
            purl = os.environ.get('JENKINS_URL')
            if purl:
                return purl.rstrip('/') + '/jnlpJars/jenkins-cli.jar'
            purl = os.environ.get('HUDSON_URL')
            if purl:
                return purl.rstrip('/') + '/jnlpJars/hudson-cli.jar'
            # If neither JENKINS nor HUDSON URL is set, assume jenkins for testing
            return "http://" + socket.getfqdn() + ':' + repr(8080) + '/jnlpJars/jenkins-cli.jar'
        else:
            return Urls._script_dir()

    @staticmethod
    def proxied_public_cli_url(api_type):
        # Not required to be a real url
        if api_type != ApiType.SCRIPT:
            # If neither JENKINS nor HUDSON URL is set, assume jenkins for testing
            cli = '/jnlpJars/hudson-cli.jar' if os.environ.get('HUDSON_URL') else '/jnlpJars/jenkins-cli.jar'
            return Urls.proxied_public_url + cli
        else:
            return Urls._script_dir()

    @staticmethod
    def _script_dir():
        sdir = os.environ.get(Urls.script_dir_env_var_name)
        return dirs.job_script_dir if sdir is None else sdir.rstrip('/')
