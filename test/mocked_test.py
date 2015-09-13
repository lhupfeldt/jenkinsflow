# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import sys
major_version = sys.version_info.major
from pytest import raises

from jenkinsflow.mocked import _mocked, mock_speedup_env_var_name


def test_mocked_bad_env_val(mock_speedup_bad_value):
    with raises(ValueError) as exinfo:
        _mocked()

    assert str(exinfo.value) == "could not convert string to float: {value}. If {env_var_name} is specied, the value must be set to the mock speedup, e.g. 2000 if you have a reasonably fast computer. If you experience FlowTimeoutException in tests, try lowering the value.".format(
        value="true" if major_version < 3 else "'true'", env_var_name=mock_speedup_env_var_name)


def test_mocked_good_env_val(mock_speedup_307):
    is_mocked, speedup = _mocked()
    assert is_mocked == True
    assert speedup == 307


def test_mocked_no_env_val(mock_speedup_none):
    is_mocked, speedup = _mocked()
    assert is_mocked == False
    assert speedup == 1
