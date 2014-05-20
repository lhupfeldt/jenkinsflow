import os

from .. mocked import env_var_prefix, mock_speedup_env_var_name

MOCK_SPEEDUP_NAME = mock_speedup_env_var_name
DIRECT_URL_NAME = env_var_prefix + 'DIRECT_URL'
USE_JENKINSAPI_NAME = env_var_prefix + 'USE_JENKINSAPI'
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


def use_jenkinsapi():
    return os.environ.get(USE_JENKINSAPI_NAME) == 'true'


def skip_job_delete():
    return os.environ.get(SKIP_JOB_DELETE_NAME) == 'true'


def skip_job_load():
    return os.environ.get(SKIP_JOB_LOAD_NAME) == 'true'


def skip_job_load_sh_export_str():
    return 'export ' + SKIP_JOB_LOAD_NAME + '=true'
