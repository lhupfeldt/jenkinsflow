import os
import pytest
from framework.jenkins_launcher import JenkinsLancher


def _set_env_fixture(var_name, value, request):
    """
    Ensure env var_name is set to the value <value>
    Set back to original value, if any, or unset it, after test
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


def _set_env_if_not_set_fixture(var_name, not_set_value, request):
    """
    Ensure env var_name is set to the value 'not_set_value' IFF it was not already set
    Set back to original value, if any, or unset it, after test
    """
    has_var = os.environ.get(var_name)
    if not has_var:
        os.environ[var_name] = not_set_value
        def fin():
            del os.environ[var_name]
        request.addfinalizer(fin)


def _unset_env_fixture(var_name, request):
    """
    Ensure env var_name is NOT set
    Set back to original value, if any, after test
    """
    has_var = os.environ.get(var_name)
    if has_var:
        del os.environ[var_name]
        def fin():
            os.environ[var_name] = has_var
        request.addfinalizer(fin)


@pytest.fixture
def mock_api_bad_value(request):
    _set_env_fixture('JENKINSFLOW_MOCK_API', 'true', request)


@pytest.fixture
def mock_api_307(request):
    _set_env_fixture('JENKINSFLOW_MOCK_API', '307', request)


@pytest.fixture
def mock_api_none(request):
    _unset_env_fixture('JENKINSFLOW_MOCK_API', request)


@pytest.fixture
def env_base_url(request):
    # Fake that we are running from inside jenkins job
    if os.environ.get('HUDSON_URL') is None:
        _set_env_if_not_set_fixture('JENKINS_URL', 'http://localhost:8080', request)


@pytest.fixture
def env_no_base_url(request):
    # Make sure it looks as if we are we are running from outside jenkins job
    _unset_env_fixture('JENKINS_URL', request)
    _unset_env_fixture('HUDSON_URL', request)


@pytest.fixture
def env_job_name(request):
    # Fake that we are running from inside jenkins job
    _set_env_if_not_set_fixture('JOB_NAME', 'hudelihuu', request)


@pytest.fixture
def env_build_number(request):
    # Fake that we are running from inside jenkins job
    _set_env_if_not_set_fixture('BUILD_NUMBER', '1', request)


@pytest.fixture(scope="module")
def fake_java(request):
    if not os.environ.get('BUILD_URL'):
        # Running outside of Jenkins, fake call to java - cli, use script ./framework/java
        here = os.path.abspath(os.path.dirname(__file__))
        orig_path = os.environ.get('PATH')
        os.environ['PATH'] = os.path.join(here, 'framework') + ':' + orig_path or ''

        if orig_path:
            def fin():
                os.environ['PATH'] = orig_path
            request.addfinalizer(fin)


@pytest.fixture(scope='session', autouse=True)
def jenkins_server(request):
    """
    Downloads and starts Jenkins
    """
    state = {}
    def stop_jenkins():
        state['launcher'].stop()

    jenkins_url = os.environ.get('JENKINS_URL') or os.environ.get('HUDSON_URL')
    if not jenkins_url:
        systests_dir, _ = os.path.split(__file__)
        war_path = os.path.join(systests_dir, 'jenkins.war')
        state['launcher'] = JenkinsLancher(war_path, [])
        state['launcher'].start()
        jenkins_url = state['launcher'].url
        request.addfinalizer(stop_jenkins)

    return jenkins_url
