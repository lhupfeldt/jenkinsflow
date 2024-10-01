# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import os
import sys
import re
from itertools import chain
from typing import List

import pytest
from pytest import fixture  # pylint: disable=no-name-in-module
from click.testing import CliRunner

from .framework import pytest_options
from .framework.cfg import ApiType, opts_to_test_cfg

# Note: You can't (indirectly) import stuff from jenkinsflow here, it messes up the coverage


# Singleton config
TEST_CFG = None


def pytest_addoption(parser):
    """pytest hook"""
    pytest_options.add_options(parser)


def pytest_configure(config):
    global TEST_CFG

    """pytest hook"""
    # Register api  marker
    config.addinivalue_line("markers", "apis(*ApiType): mark test to run only when using specified apis")
    config.addinivalue_line("markers", "not_apis(*ApiType): mark test NOT to run when using specified apis")

    TEST_CFG = opts_to_test_cfg(
        config.getoption(pytest_options.OPT_DIRECT_URL),
        config.getoption(pytest_options.OPT_JOB_LOAD),
        config.getoption(pytest_options.OPT_JOB_DELETE),
        config.getoption(pytest_options.OPT_MOCK_SPEEDUP),
        config.getoption(pytest_options.OPT_API),
    )
    config.cuctom_cfg = TEST_CFG


def pytest_collection_modifyitems(items: List[pytest.Item], config) -> None:
    """pytest hook"""
    selected_api_types = config.cuctom_cfg.apis
    item_api_type_regex = re.compile(r'.*\[ApiType\.(.*)\]')
    remaining = []
    deselected = []

    def filter_items_by_api_type(item):
        if "api_type" not in item.fixturenames:
            for om in item.own_markers:
                if om.name in ("apis", "not_apis"):
                    location = ':'.join(str(place) for place in item.location)
                    raise Exception(f"{location}: Error: A test using the 'apis' or 'not_apis' marker must also use the 'api_type' fixture.")
            remaining.append(item)
            return

        # We must have an ApiType in name now, since api_type fixture was used
        current_item_api = ApiType[item_api_type_regex.match(item.name).groups()[0]]
        if current_item_api not in selected_api_types:
            print(f"{':'.join(str(place) for place in item.location)} DESELECTED ({current_item_api} not in {selected_api_types})")
            deselected.append(item)
            return

        remaining.append(item)


    print()
    for item in items:
        filter_items_by_api_type(item)

    if deselected:
        config.hook.pytest_deselected(items=deselected)
        items[:] = remaining


@pytest.fixture()
def options():
    """Access to test configuration objects."""
    return TEST_CFG


@pytest.fixture(params=list(ApiType))
def api_type(request, options):
    """ApiType fixture"""
    selected_api_type = request.param
    assert isinstance(selected_api_type, ApiType)

    for apimarker in request.node.iter_markers("apis"):
        apis = apimarker.args
        for allowed_api_type in apis:
            assert isinstance(allowed_api_type, ApiType)

        if selected_api_type not in apis:
            pytest.skip(f"only for {apis} APIs, current {selected_api_type}")
            return selected_api_type

    for not_apimarker in request.node.iter_markers("not_apis"):
        not_apis = not_apimarker.args
        for not_api_type in not_apis:
            assert isinstance(not_api_type, ApiType)

        if selected_api_type in not_apis:
            pytest.skip(f"not for {not_apis} APIs, current {selected_api_type}")
            return selected_api_type

    return selected_api_type


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
def env_base_url(request, api_type, options):
    # Fake that we are running from inside jenkins job
    public_url = options.urls.public_url(api_type)
    _set_jenkins_url_env_if_not_set_fixture(public_url, request)
    return public_url


@fixture
def env_base_url_trailing_slash(request, api_type, options):
    _set_jenkins_url_env_if_not_set_fixture(options.urls.public_url(api_type) + '/', request)


@fixture
def env_base_url_trailing_slashes(request, api_type, options):
    _set_jenkins_url_env_if_not_set_fixture(options.urls.public_url(api_type) + '//', request)


@fixture
def env_no_base_url(request):
    # Make sure it looks as if we are we are running from outside jenkins job
    _unset_env_fixture('JENKINS_URL', request)
    _unset_env_fixture('HUDSON_URL', request)


@fixture
def env_different_base_url(request, options):
    # Fake that we are running from inside jenkins job
    # This url is not used, but should simply be different fron direct_url used in test, to simulate proxied jenkins
    _set_jenkins_url_env_fixture(options.urls.proxied_public_url, request)


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
