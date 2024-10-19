class JobLoad():
    def __init__(self, load_jobs: bool, delete_jobs: bool):
        self.load_jobs = load_jobs
        self.delete_jobs = delete_jobs

    def skip_job_delete(self):
        return not self.delete_jobs

    def skip_job_load(self):
        return not self.load_jobs

    def skip_job_load_sh_export_str(self):
        return 'export ' + JobLoad.skip_job_load_env_var_name + '=true'
