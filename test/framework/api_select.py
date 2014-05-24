# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

import os, sys, re
from os.path import join as jp

here = os.path.abspath(os.path.dirname(__file__))
sys.path.extend([jp(here, '../../..'), jp(here, '../../demo')])

from jenkinsflow.mocked import mocked
from jenkinsflow.test import cfg as test_cfg

from jenkinsflow.unbuffered import UnBuffered
sys.stdout = UnBuffered(sys.stdout)

_file_name_subst = re.compile(r'(_jobs|_test)?\.py')


def api(file_name, login=False, fixed_prefix=None):
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
    if mocked:
        print('Using Mocked API')
        from .mock_api import MockApi
        return MockApi(job_name_prefix, test_cfg.direct_url())
    else:
        if test_cfg.use_specialized_api():
            print('Using Specialized Jenkins API with wrapper')
        elif test_cfg.use_jenkinsapi():
            print('Using JenkinsAPI with wrapper')
        elif test_cfg.use_script_api():
            print('Using Script API with wrapper')

        reload_jobs = not test_cfg.skip_job_load() and not fixed_prefix
        pre_delete_jobs = not test_cfg.skip_job_delete()
        import demo_security as security
        from .api_wrapper import JenkinsTestWrapperApi
        return JenkinsTestWrapperApi(file_name, func_name, func_num_params, job_name_prefix, reload_jobs, pre_delete_jobs,
                                     test_cfg.direct_url(), security.username, security.password, security.securitytoken, login=login)
