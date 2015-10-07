import os, socket
from enum import Enum

env_var_prefix = "JENKINSFLOW_"

from .framework import config

DIRECT_URL_NAME = env_var_prefix + 'DIRECT_URL'
SCRIPT_DIR_NAME = env_var_prefix + 'SCRIPT_DIR'

SKIP_JOB_LOAD_NAME = env_var_prefix + 'SKIP_JOB_LOAD'
SKIP_JOB_DELETE_NAME = env_var_prefix + 'SKIP_JOB_DELETE'


class ApiType(Enum):
    JENKINS = 0
    SCRIPT = 1
    MOCK = 2


_speedup = 1


def direct_url(api_type):
    if api_type != ApiType.SCRIPT:
        durl = os.environ.get(DIRECT_URL_NAME)
        return 'http://localhost:8080' if durl is None else durl.rstrip('/')
    else:
        return script_dir()


def public_url(api_type):
    if api_type != ApiType.SCRIPT:
        purl = os.environ.get('JENKINS_URL') or os.environ.get('HUDSON_URL')
        return "http://" + socket.getfqdn() + ':' + repr(8080) + '/' if purl is None else purl
    else:
        return script_dir()


def direct_cli_url(api_type):
    if api_type != ApiType.SCRIPT:
        purl = os.environ.get('JENKINS_URL')
        if purl:
            return direct_url(api_type) + '/jnlpJars/jenkins-cli.jar'
        purl = os.environ.get('HUDSON_URL')
        if purl:
            return direct_url(api_type) + '/jnlpJars/hudson-cli.jar'
        # If neither JENKINS nor HUDSON URL is set, assume jenkins for testing
        return direct_url(api_type) + '/jnlpJars/jenkins-cli.jar'
    else:
        return script_dir()


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
        return script_dir()


proxied_public_url = "http://myproxy.mydom/jenkins"


def proxied_public_cli_url(api_type):
    # Not required to be a real url
    if api_type != ApiType.SCRIPT:
        # If neither JENKINS nor HUDSON URL is set, assume jenkins for testing
        cli = '/jnlpJars/hudson-cli.jar' if os.environ.get('HUDSON_URL') else '/jnlpJars/jenkins-cli.jar'
        return proxied_public_url + cli
    else:
        return script_dir()


def script_dir():
    sdir = os.environ.get(SCRIPT_DIR_NAME)
    return config.job_script_dir if sdir is None else sdir.rstrip('/')


def select_speedup(speedup):
    """speedup is used by the mock api"""
    global _speedup
    _speedup = speedup


def speedup():
    return _speedup


def skip_job_delete():
    return os.environ.get(SKIP_JOB_DELETE_NAME) == 'true'


def skip_job_load():
    return os.environ.get(SKIP_JOB_LOAD_NAME) == 'true'


def skip_job_load_sh_export_str():
    return 'export ' + SKIP_JOB_LOAD_NAME + '=true'
