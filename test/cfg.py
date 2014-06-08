import os

from .. mocked import env_var_prefix, mock_speedup_env_var_name
from .framework import config

MOCK_SPEEDUP_NAME = mock_speedup_env_var_name
DIRECT_URL_NAME = env_var_prefix + 'DIRECT_URL'
SCRIPT_DIR_NAME = env_var_prefix + 'SCRIPT_DIR'

USE_SPECIALIZED_API_NAME = env_var_prefix + 'USE_SPECIALIZED_API'
USE_JENKINS_API_NAME = env_var_prefix + 'USE_JENKINS_API'
USE_SCRIPT_API_NAME = env_var_prefix + 'USE_SCRIPT_API'

SKIP_JOB_LOAD_NAME = env_var_prefix + 'SKIP_JOB_LOAD'
SKIP_JOB_DELETE_NAME = env_var_prefix + 'SKIP_JOB_DELETE'


def mock(speedup):
    assert isinstance(speedup, (int, float))
    os.environ[MOCK_SPEEDUP_NAME] = str(speedup)


def unmock():
    del os.environ[MOCK_SPEEDUP_NAME]


def direct_url():
    durl = os.environ.get(DIRECT_URL_NAME)
    return 'http://localhost:8080' if durl is None else durl.rstrip('/')


def script_dir():
    sdir = os.environ.get(SCRIPT_DIR_NAME)
    return config.job_script_dir if sdir is None else sdir.rstrip('/')


def use_specialized_api():
    return os.environ.get(USE_SPECIALIZED_API_NAME) == 'true'


def use_jenkinsapi():
    return os.environ.get(USE_JENKINS_API_NAME) == 'true'


def use_script_api():
    return os.environ.get(USE_SCRIPT_API_NAME) == 'true'


def skip_job_delete():
    return os.environ.get(SKIP_JOB_DELETE_NAME) == 'true'


def skip_job_load():
    return os.environ.get(SKIP_JOB_LOAD_NAME) == 'true'


def skip_job_load_sh_export_str():
    return 'export ' + SKIP_JOB_LOAD_NAME + '=true'
