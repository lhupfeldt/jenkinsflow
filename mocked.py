import os, time

env_var_prefix = "JENKINSFLOW_"
mock_api_env_var_name = env_var_prefix + 'MOCK_SPEEDUP'


def mocked():
    mock_val = os.environ.get(mock_api_env_var_name)
    if mock_val is None:
        return False, 1.0

    try:
        return True, max(1.0, float(mock_val))
    except ValueError as ex:
        msg = "If " + mock_api_env_var_name + " is specied, the value must be set to the mock speedup, e.g. 2000 if you have a reasonably fast computer."
        msg += " If you experience FlowTimeoutException in tests, try lowering the value."
        raise ValueError(str(ex) + ". " + msg)


class HyperSpeed(object):
    def __init__(self):
        self.is_mocked, self.speedup = mocked()

    def time(self):
        return time.time() * self.speedup

    def sleep(self, seconds):
        return time.sleep(seconds / self.speedup)
