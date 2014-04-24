import os

from .. mocked import _env_var_prefix, _mock_api_env_var_name


def mock_default():
    os.environ.setdefault(_mock_api_env_var_name, '100')


def unmock():
    del os.environ[_mock_api_env_var_name]


def direct_url():
    durl = os.environ.get(_env_var_prefix + 'DIRECT_URL')
    return 'http://localhost:8080' if durl is None else durl.rstrip('/')


def use_jenkinsapi():
    return os.environ.get(_env_var_prefix + 'USE_JENKINSAPI') == 'true'


def skip_job_load():
    return os.environ.get(_env_var_prefix + 'SKIP_JOB_LOAD') == 'true'


def skip_job_load_sh_export_str():
    return 'export ' + _env_var_prefix + 'SKIP_JOB_LOAD=true'


def skip_job_delete():
    return os.environ.get(_env_var_prefix + 'SKIP_JOB_DELETE') == 'true'
