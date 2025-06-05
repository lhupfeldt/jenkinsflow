# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from pathlib import Path

import pytest

from jenkinsflow.flow import serial, FailedChildJobException

from .framework import api_select
from .framework.cfg import ApiType


_HERE = Path(__file__).resolve().parent
_FRAMEWORK_DIR = _HERE/"framework"


@pytest.mark.apis(ApiType.JENKINS)
def test_early_set_result(api_type):
    """Make sure we keep checking until we have the final result, not an intermediate one."""
    with api_select.api(__file__, api_type) as api:
        api.job('wait10', max_fails=1, expect_invocations=1, expect_order=1, exec_time=10, serial=True, job_xml_template=_FRAMEWORK_DIR/"pipeline_job.xml.tenjin")

        with pytest.raises(FailedChildJobException):
            with serial(api, timeout=40, job_name_prefix=api.job_name_prefix, report_interval=1) as ctrl:
                ctrl.invoke('wait10')
