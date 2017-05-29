# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from pytest import raises

from .framework import api_select
from jenkinsflow.flow import serial, FailedChildJobException


def test_hide_password_failed_job(api_type, capsys):
    with api_select.api(__file__, api_type) as api:
        api.flow_job()
        api.job('passwd_args', max_fails=1, expect_invocations=1, expect_order=1,
                params=(('s1', 'no-secret', 'desc'), ('passwd', 'p2', 'desc'), ('PASS', 'p3', 'desc')))

        with raises(FailedChildJobException) as exinfo:
            with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=3, secret_params='.*PASS.*|.*pass.*') as ctrl:
                # NOTE: In order to ensure that passwords are not displayed in a stacktrace you must never put a literal password
                # In the last line in the with statement, or in any statement that may raise an exception. You shold not really
                # put clear text paswords in you code anyway :)
                p1, p2, p3 = 'SECRET', 'hemmeligt', 'not_security'
                ctrl.invoke('passwd_args', password=p1, s1='no-secret', passwd=p2, PASS=p3)

        sout, _ = capsys.readouterr()
        assert '******' in sout
        assert 'no-secret' in sout
        assert p1 not in sout
        assert p2 not in sout
        assert p3 not in sout

        assert p1 not in str(exinfo.value)
        assert p2 not in str(exinfo.value)
        assert p3 not in str(exinfo.value)
