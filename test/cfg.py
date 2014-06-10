import os
from enum import Enum

# Duplicated from .. mocked, can't import that here because of coverage test issues
env_var_prefix = "JENKINSFLOW_"
mock_speedup_env_var_name = env_var_prefix + 'MOCK_SPEEDUP'

from .framework import config

MOCK_SPEEDUP_NAME = mock_speedup_env_var_name
DIRECT_URL_NAME = env_var_prefix + 'DIRECT_URL'
SCRIPT_DIR_NAME = env_var_prefix + 'SCRIPT_DIR'

SKIP_JOB_LOAD_NAME = env_var_prefix + 'SKIP_JOB_LOAD'
SKIP_JOB_DELETE_NAME = env_var_prefix + 'SKIP_JOB_DELETE'


class ApiType(Enum):
    SPECIALIZED = 0
    SCRIPT = 1
    JENKINSAPI = 2
    MOCK = 3

    def env_name(self):
        return str(self).replace('.', '_')
    

def mock(speedup):
    assert isinstance(speedup, (int, float))
    os.environ[MOCK_SPEEDUP_NAME] = str(speedup)


def unmock():
    del os.environ[MOCK_SPEEDUP_NAME]


def direct_url():
    if selected_api() != ApiType.SCRIPT:
        durl = os.environ.get(DIRECT_URL_NAME)
        return 'http://localhost:8080' if durl is None else durl.rstrip('/')
    else:
        return script_dir()


def script_dir():
    sdir = os.environ.get(SCRIPT_DIR_NAME)
    return config.job_script_dir if sdir is None else sdir.rstrip('/')


def select_api(api):
    for aa in ApiType:
        os.environ[aa.env_name()] = 'false'
    os.environ[api.env_name()] = 'true'


def selected_api():
    count = 0
    found_api = None
    for api in ApiType:
        if os.environ.get(api.env_name()) == 'true':
            found_api = api
            count += 1
    if count == 1:
        return found_api
    raise Exception("Error: " + ("No api selected" if not count else repr(count) + " apis selected"))


def skip_job_delete():
    return os.environ.get(SKIP_JOB_DELETE_NAME) == 'true'


def skip_job_load():
    return os.environ.get(SKIP_JOB_LOAD_NAME) == 'true'


def skip_job_load_sh_export_str():
    return 'export ' + SKIP_JOB_LOAD_NAME + '=true'
