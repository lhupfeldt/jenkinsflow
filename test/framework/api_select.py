# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import os, sys, re

from jenkinsflow.unbuffered import UnBuffered

from ..conftest import get_cfg

from .cfg import ApiType, AllCfg
from .cfg.speedup import speedup


sys.stdout = UnBuffered(sys.stdout)

_file_name_subst = re.compile(r'(_jobs|_test)?\.py')


def api(file_name, api_type, login=None, fixed_prefix=None, url_or_dir=None, fake_public_uri=None, invocation_class=None,
        username=None, password=None, *, options: AllCfg = None, existing_jobs: bool = False):
    """Factory to create either Mock or Wrap api"""
    options = options or get_cfg()
    base_name = os.path.basename(file_name).replace('.pyc', '.py')
    job_name_prefix = _file_name_subst.sub('', base_name)
    func_name = None
    func_num_params = 0
    if existing_jobs:
        job_name_prefix = ""
        file_name = base_name
    elif fixed_prefix:
        job_name_prefix = fixed_prefix
        file_name = base_name
    elif '_test' in file_name:
        func_name = sys._getframe().f_back.f_code.co_name  # pylint: disable=protected-access
        func_num_params = sys._getframe().f_back.f_code.co_argcount  # pylint: disable=protected-access
        file_name = base_name
        func_name = func_name.replace('test_', '')
        assert func_name[0:len(job_name_prefix)] == job_name_prefix, \
            "Naming standard not followed: " + repr('test_' + func_name) + " defined in file: " + repr(base_name) + " should be 'test_" + job_name_prefix + "_<sub test>'"
        job_name_prefix = 'jenkinsflow_test__' + func_name + '__'
    else:
        job_name_prefix = 'jenkinsflow_demo__' + job_name_prefix + '__'
        file_name = base_name.replace('_jobs', '')

    print()
    print("--- Preparing api for ", repr(job_name_prefix), "---")

    if api_type == 0:
        # Invocation from actual Jenkins flow job calls with api_type == 0
        api_type = ApiType.JENKINS
    print('Using:', api_type)

    url_or_dir = url_or_dir or options.urls.direct_url(api_type)
    reload_jobs = not options.job_load.skip_job_load() and not fixed_prefix and not existing_jobs
    pre_delete_jobs = not options.job_load.skip_job_delete()

    from .cfg import jenkins_security
    if login is None:
        login = jenkins_security.default_use_login

    if password is not None or username is not None:
        assert password is not None and username is not None
        login = True

    if username is None:
        assert password is None
        username = jenkins_security.username
        password = jenkins_security.password

    if api_type == ApiType.JENKINS:
        from .api_wrapper import JenkinsTestWrapperApi
        return JenkinsTestWrapperApi(
            file_name=file_name,
            func_name=func_name,
            func_num_params=func_num_params,
            job_name_prefix=job_name_prefix,
            reload_jobs=reload_jobs,
            pre_delete_jobs=pre_delete_jobs,
            direct_url=url_or_dir,
            fake_public_uri=fake_public_uri,
            username=username,
            password=password,
            securitytoken=jenkins_security.securitytoken,
            login=login,
            invocation_class=invocation_class,
            python_executable=os.environ["JEKINSFLOW_TEST_JENKINS_API_PYTHON_EXECUTABLE"],
            existing_jobs=existing_jobs)

    if api_type == ApiType.SCRIPT:
        from .api_wrapper import ScriptTestWrapperApi
        return ScriptTestWrapperApi(
            file_name=file_name,
            func_name=func_name,
            func_num_params=func_num_params,
            job_name_prefix=job_name_prefix,
            reload_jobs=reload_jobs,
            pre_delete_jobs=pre_delete_jobs,
            direct_url=url_or_dir,
            fake_public_uri=fake_public_uri,
            username=username,
            password=password,
            securitytoken=jenkins_security.securitytoken,
            login=login,
            invocation_class=invocation_class)

    if api_type == ApiType.MOCK:
        from .mock_api import MockApi
        return MockApi(
            job_name_prefix=job_name_prefix,
            speedup=speedup(),
            public_uri=options.urls.direct_url(api_type),
            python_executable=sys.executable)

    raise Exception(f"Unhandled api_type: {repr(api_type)} - {api_type.__class__.__module__} was compared to {ApiType.MOCK.__class__.__module__}")
