# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import os, sys, re
from os.path import join as jp

here = os.path.abspath(os.path.dirname(__file__))
sys.path.extend([jp(here, '../../..'), jp(here, '../../demo')])

from jenkinsflow.test import cfg as test_cfg

from jenkinsflow.unbuffered import UnBuffered
sys.stdout = UnBuffered(sys.stdout)

_file_name_subst = re.compile(r'(_jobs|_test)?\.py')


def api(file_name, api_type, login=None, fixed_prefix=None, url_or_dir=None, fake_public_uri=None, invocation_class=None,
        username=None, password=None):
    """Factory to create either Mock or Wrap api"""
    base_name = os.path.basename(file_name).replace('.pyc', '.py')
    job_name_prefix = _file_name_subst.sub('', base_name)
    func_name = None
    func_num_params = 0
    if fixed_prefix:
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
        api_type = test_cfg.ApiType.JENKINS
    print('Using:', api_type)

    url_or_dir = url_or_dir or test_cfg.direct_url(api_type)
    reload_jobs = not test_cfg.skip_job_load() and not fixed_prefix
    pre_delete_jobs = not test_cfg.skip_job_delete()

    import demo_security as security
    if login is None:
        login = security.default_use_login

    if password is not None or username is not None:
        assert password is not None and username is not None
        login = True

    if username is None:
        assert password is None
        username = security.username
        password = security.password

    if api_type == test_cfg.ApiType.JENKINS:
        from .api_wrapper import JenkinsTestWrapperApi
        return JenkinsTestWrapperApi(file_name, func_name, func_num_params, job_name_prefix, reload_jobs, pre_delete_jobs,
                                     url_or_dir, fake_public_uri, username, password, security.securitytoken, login=login,
                                     invocation_class=invocation_class)
    if api_type == test_cfg.ApiType.SCRIPT:
        from .api_wrapper import ScriptTestWrapperApi
        return ScriptTestWrapperApi(file_name, func_name, func_num_params, job_name_prefix, reload_jobs, pre_delete_jobs,
                                    url_or_dir, fake_public_uri, username, password, security.securitytoken, login=login,
                                    invocation_class=invocation_class)
    if api_type == test_cfg.ApiType.MOCK:
        from .mock_api import MockApi
        return MockApi(job_name_prefix, test_cfg.speedup(), test_cfg.direct_url(api_type))

    raise Exception("Unhandled api_type:" + repr(api_type))
