# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from jenkinsflow.flow import serial

import pytest

from .framework import api_select
from .framework.cfg import ApiType


@pytest.mark.apis(ApiType.JENKINS)
def test_multiple_apis_mixed(api_type, options):
    _params = (('password', '', 'Some password'), ('s1', '', 'Some string argument'))

    if ApiType.SCRIPT not in options.apis:
        pytest.skip(f"Requires both {ApiType.JENKINS} and {ApiType.SCRIPT}")

    with api_select.api(__file__, api_type) as jenkins_api1:
        jenkins_api1.flow_job()

        jenkins_api1.job('job-1', max_fails=0, expect_invocations=1, expect_order=1, params=_params)
        jenkins_api1.job('job-3', max_fails=0, expect_invocations=1, expect_order=3)
        jenkins_api1.job('job-5', max_fails=0, expect_invocations=1, expect_order=3)
        jenkins_api1.job('job-7', max_fails=0, expect_invocations=1, expect_order=4, serial=True)

        with api_select.api(__file__, ApiType.SCRIPT) as script_api1:
            script_api1.job('job-2', max_fails=0, expect_invocations=1, expect_order=2, serial=True)
            script_api1.job('job-4', max_fails=0, expect_invocations=1, expect_order=3)
            script_api1.job('job-6', max_fails=0, expect_invocations=1, expect_order=3, params=_params, serial=True)

            with api_select.api(__file__, ApiType.JENKINS) as jenkins_api2:
                jenkins_api2.job('job-8', max_fails=0, expect_invocations=1, expect_order=3, serial=True)
                jenkins_api2.job('job-9', max_fails=0, expect_invocations=1, expect_order=3)

                # Flow
                with serial(jenkins_api1, timeout=70, job_name_prefix=jenkins_api1.job_name_prefix, report_interval=1) as ctrl1:
                    ctrl1.invoke('job-1', password='a', s1='b')
                    with ctrl1.serial(api=script_api1) as sc_ctrl:
                        sc_ctrl.invoke('job-2')

                    with ctrl1.parallel(timeout=40, report_interval=3) as ctrl2:
                        with ctrl2.serial(timeout=40, report_interval=3) as ctrl3a:
                            ctrl3a.invoke('job-3')

                        with ctrl2.serial(api=script_api1, timeout=40, report_interval=3) as ctrl3a:
                            ctrl3a.invoke('job-6', password='a', s1='b')

                        with ctrl2.parallel(timeout=40, report_interval=3) as ctrl3b:
                            with ctrl3b.serial(api=script_api1, report_interval=0.5) as ctrl4:
                                ctrl4.invoke('job-4')
                            ctrl3b.invoke('job-5')

                        with ctrl2.parallel(api=jenkins_api2, timeout=40) as ctrl3c:
                            ctrl3c.invoke('job-8')
                            ctrl3c.invoke('job-9')

                    ctrl1.invoke('job-7')
