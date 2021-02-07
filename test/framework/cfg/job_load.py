import os

from .os_env import ENV_VAR_PREFIX


class JobLoad():
    skip_job_load_env_var_name = ENV_VAR_PREFIX + 'SKIP_JOB_LOAD'
    skip_job_delete_env_var_name = ENV_VAR_PREFIX + 'SKIP_JOB_DELETE'

    @staticmethod
    def skip_job_delete():
        return os.environ.get(JobLoad.skip_job_delete_env_var_name) == 'true'

    @staticmethod
    def skip_job_load():
        return os.environ.get(JobLoad.skip_job_load_env_var_name) == 'true'

    @staticmethod
    def skip_job_load_sh_export_str():
        return 'export ' + JobLoad.skip_job_load_env_var_name + '=true'
