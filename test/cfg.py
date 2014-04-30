import os

from .. mocked import env_var_prefix, mock_api_env_var_name


def mock(speedup):
    assert isinstance(speedup, (int, float))
    os.environ[mock_api_env_var_name] = str(speedup)


def unmock():
    del os.environ[mock_api_env_var_name]


def direct_url():
    durl = os.environ.get(env_var_prefix + 'DIRECT_URL')
    return 'http://localhost:8080' if durl is None else durl.rstrip('/')


def use_jenkinsapi():
    return os.environ.get(env_var_prefix + 'USE_JENKINSAPI') == 'true'


def skip_job_load():
    return os.environ.get(env_var_prefix + 'SKIP_JOB_LOAD') == 'true'


def skip_job_load_sh_export_str():
    return 'export ' + env_var_prefix + 'SKIP_JOB_LOAD=true'


def skip_job_delete():
    return os.environ.get(env_var_prefix + 'SKIP_JOB_DELETE') == 'true'
