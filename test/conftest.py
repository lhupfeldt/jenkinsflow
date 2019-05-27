# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import os

import pytest
from pytest import fixture  # pylint: disable=no-name-in-module
from click.testing import CliRunner

from . import cfg as test_cfg
from .cfg import ApiType

# Note: You can't (indirectly) import stuff from jenkinsflow here, it messes up the coverage


@pytest.fixture(params=[ApiType.MOCK, ApiType.JENKINS, ApiType.SCRIPT])
def api_type(request):
    """ApiType fixture"""
    selected_api_type = request.param    

    for apimarker in request.node.iter_markers("apis"):
        apis = apimarker.args
        if selected_api_type not in apis:
            pytest.skip("test requires one the following apis {apis}, current {api_type}".format(apis=apis, api_type=selected_api_type))

    for not_apimarker in request.node.iter_markers("not_apis"):
        not_apis = not_apimarker.args
        if selected_api_type in not_apis:
            pytest.skip("test is not run for the following apis {apis}, current {api_type}".format(apis=not_apis, api_type=selected_api_type))

    return selected_api_type


def pytest_configure(config):
    # Register api  marker
    config.addinivalue_line("markers", "apis(*ApiType): mark test to run only when using specified apis")
    config.addinivalue_line("markers", "not_apis(*ApiType): mark test NOT to run when using specified apis")


def _set_env_fixture(var_name, value, request):
    """
    Ensure env var_name is set to the value <value>
    Set back to original value, if any, or unset it, after test.
    """
    has_var = os.environ.get(var_name)
    os.environ[var_name] = value
    if not has_var:
        def fin():
            del os.environ[var_name]
    else:
        def fin():
            os.environ[var_name] = has_var
    request.addfinalizer(fin)


def _set_jenkins_url_env_fixture(not_set_value, request):
    if os.environ.get('JENKINS_URL'):
        _set_env_fixture('JENKINS_URL', not_set_value, request)
        return

    _set_env_fixture('HUDSON_URL', not_set_value, request)


def _set_env_if_not_set_fixture(var_name, not_set_value, request):
    """
    Ensure env var_name is set to the value 'not_set_value' IFF it was not already set.
    Unset it after test.
    """
    has_var = os.environ.get(var_name)
    if not has_var:
        os.environ[var_name] = not_set_value
        def fin():
            del os.environ[var_name]
        request.addfinalizer(fin)


def _set_jenkins_url_env_if_not_set_fixture(not_set_value, request):
    if not os.environ.get('HUDSON_URL'):
        _set_env_if_not_set_fixture('JENKINS_URL', not_set_value, request)


def _unset_env_fixture(var_name, request):
    """
    Ensure env var_name is NOT set
    Set back to original value, if any, after test.
    """
    has_var = os.environ.get(var_name)
    if has_var:
        del os.environ[var_name]
        def fin():
            os.environ[var_name] = has_var
        request.addfinalizer(fin)


@fixture
def env_base_url(request, api_type):
    # Fake that we are running from inside jenkins job
    public_url = test_cfg.public_url(api_type)
    _set_jenkins_url_env_if_not_set_fixture(public_url, request)
    return public_url


@fixture
def env_base_url_trailing_slash(request, api_type):
    _set_jenkins_url_env_if_not_set_fixture(test_cfg.public_url(api_type) + '/', request)


@fixture
def env_base_url_trailing_slashes(request, api_type):
    _set_jenkins_url_env_if_not_set_fixture(test_cfg.public_url(api_type) + '//', request)


@fixture
def env_no_base_url(request):
    # Make sure it looks as if we are we are running from outside jenkins job
    _unset_env_fixture('JENKINS_URL', request)
    _unset_env_fixture('HUDSON_URL', request)


@fixture
def env_different_base_url(request):
    # Fake that we are running from inside jenkins job
    # This url is not used, but should simply be different fron direct_url used in test, to simulate proxied jenkins
    _set_jenkins_url_env_fixture(test_cfg.proxied_public_url, request)


@fixture
def env_job_name(request):
    # Fake that we are running from inside jenkins job
    _set_env_if_not_set_fixture('JOB_NAME', 'hudelihuu', request)


@fixture
def env_build_number(request):
    # Fake that we are running from inside jenkins job
    _set_env_if_not_set_fixture('BUILD_NUMBER', '1', request)


@fixture(scope='function')
def cli_runner(request):
    return CliRunner()
