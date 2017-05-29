# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from jenkinsflow.flow import serial

from .framework import api_select


def test_stop_api_not_running_build(api_type):
    with api_select.api(__file__, api_type) as api:
        api.job('j1', max_fails=0, expect_invocations=1, expect_order=1)

        with serial(api, timeout=40, job_name_prefix=api.job_name_prefix, report_interval=1) as ctrl:
            ctrl.invoke('j1')

    job = api.get_job(api.job_name_prefix + "j1")
    job.stop_all()


# TODO
