# Copyright (c) 2012 - 2024 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from . import ApiType, str_to_apis, apis_to_str, Urls, JobLoad, dirs, speedup


class AllCfg():
    def __init__(self, urls: Urls, job_load: JobLoad, apis: list[ApiType]):
        self.urls = urls
        self.job_load = job_load
        self.apis = apis


def opts_to_test_cfg(direct_url: str, load_jobs: bool, delete_jobs: bool, mock_speedup: int, apis_str: str) -> AllCfg:
    urls = Urls(direct_url, dirs.job_script_dir)
    job_load = JobLoad(load_jobs, delete_jobs)

    speedup.select_speedup(mock_speedup)

    try:
        apis = str_to_apis(apis_str)
        print("APIs:", apis)
    except KeyError as ex:
        print(ex, file=sys.stderr)
        print(f"'{ex}' cannot be converted to ApiType. Should be one or more of: {','.join([at.name for at in list(ApiType)])}")
        raise

    return AllCfg(urls, job_load, apis)


def opt_strs_to_test_cfg(direct_url: str, load_jobs: str, delete_jobs: str, mock_speedup: str, apis_str: str) -> AllCfg:
    return opts_to_test_cfg(
        direct_url = direct_url,
        load_jobs = load_jobs.lower() == "true",
        delete_jobs = delete_jobs.lower() == "true",
        mock_speedup = int(mock_speedup),
        apis_str = apis_str)


def test_cfg_to_opt_strs(test_cfg: AllCfg, api_type: ApiType) -> tuple[str, str, str, str, str]:
    return (
        test_cfg.urls.direct_url(api_type),
        str(test_cfg.job_load.load_jobs).lower(),
        str(test_cfg.job_load.delete_jobs).lower(),
        str(speedup.speedup()),
        apis_to_str(test_cfg.apis),
    )
