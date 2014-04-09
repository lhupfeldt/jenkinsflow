import os

_env_var_prefix = "JENKINSFLOW_"
_mock_api_env_var_name = _env_var_prefix + 'MOCK_API'

def mocked():
    mock_val = os.environ.get(_mock_api_env_var_name)
    if mock_val is None:
        return False, 1.0

    try:
        return True, max(1.0, float(mock_val))
    except ValueError as ex:
        msg = "If JENKINSFLOW_MOCK_API is specied, the value must be set to the mock speedup, e.g. 2000 if you have a reasonably fast computer."
        msg += " If you experience FlowTimeoutException in tests, try lowering the value."
        raise ValueError(str(ex) + ". " + msg)
