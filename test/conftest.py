"""Configuration file for 'pytest'"""

import sys
import os
import re
import errno
from pathlib import Path
import shutil

import pytest
from pytest import fixture
from click.testing import CliRunner

from .framework import pytest_options
from .framework.cfg import ApiType, opts_to_test_cfg

# Note: You can't (indirectly) import stuff from jenkinsflow here, it messes up the coverage

_HERE = Path(__file__).absolute().parent
_DEMO_DIR = (_HERE/"../demo").resolve()
sys.path.append(str(_DEMO_DIR))

_OUT_DIRS = {}

def _test_key_shortener(key_prefix, key_suffix):
    prefix = key_prefix.replace('test.', '').replace('_test', '')
    suffix = key_suffix.replace(prefix, '').replace('test_', '').strip('_')
    outd = prefix + '.' + suffix
    args = (key_prefix, key_suffix)
    assert _OUT_DIRS.setdefault(outd, args) == args, \
        f"Out dir name '{outd}' reused! Previous from {_OUT_DIRS[outd]}, now  {args}. Test is not following namimg convention."
    return outd


def _test_node_shortener(request):
    """Shorten test node name while still keeping it unique"""
    return _test_key_shortener(request.node.module.__name__, request.node.name.split('[')[0])


@fixture(name="out_dir")
def _fixture_out_dir(request):
    """Create unique top level test directory for a test."""

    out_dir = _HERE/'out'/_test_node_shortener(request)

    try:
        shutil.rmtree(out_dir)
    except OSError as ex:
        if ex.errno != errno.ENOENT:
            raise

    return out_dir

# Add you configuration, e.g. fixtures here.


def pytest_addoption(parser):
    """pytest hook"""
    pytest_options.add_options(parser)


def pytest_configure(config):
    """pytest hook"""
    # Register api  marker
    config.addinivalue_line("markers", "apis(*ApiType): mark test to run only when using specified apis")
    config.addinivalue_line("markers", "not_apis(*ApiType): mark test NOT to run when using specified apis")

    config.cuctom_cfg = opts_to_test_cfg(
        config.getoption(pytest_options.OPT_DIRECT_URL),
        config.getoption(pytest_options.OPT_JOB_LOAD),
        config.getoption(pytest_options.OPT_JOB_DELETE),
        config.getoption(pytest_options.OPT_MOCK_SPEEDUP),
        config.getoption(pytest_options.OPT_API),
    )
    pytest._CUSTOM_TEST_CFG = config.cuctom_cfg


def get_cfg():
    return pytest._CUSTOM_TEST_CFG


def pytest_collection_modifyitems(items: list[pytest.Item], config) -> None:
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


@pytest.fixture(scope="session")
def options(pytestconfig):
    """Access to test configuration objects."""
    return pytestconfig.cuctom_cfg


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
