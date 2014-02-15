#!/usr/bin/python

# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from framework import mock_api
from jenkinsflow.jobcontrol import serial, FailedChildJobException


def main():
    with mock_api.api(__file__) as api:
        def job(name, params=None):
            api.job(name, exec_time=0.5, max_fails=1, expect_invocations=1, expect_order=1, params=params)

        api.flow_job('flow')
        job('passwd_args', params=(('fail', 'true', 'Force job to fail'), ('s1', 'no-secret', 'desc'), ('passwd', 'p2', 'desc'), ('PASS', 'p3', 'desc')))

        try:
            with serial(api, timeout=70, job_name_prefix=api.job_name_prefix, report_interval=3, secret_params='.*PASS.*|.*pass.*') as ctrl:
                # NOTE: In order to ensure that passwords are not displayed in a stacktrace you must never put a literal password
                # In the last line in the with statement, or in any statement that may raise an exception. You shold not really
                # put clear text paswords in you code anyway :)
                p1, p2, p3 = 'SECRET', 'sec', 'not_security'
                ctrl.invoke('passwd_args', fail='yes', password=p1, s1='no-secret', passwd=p2, PASS=p3)
            raise Exception("Should have failed!")
        except FailedChildJobException as ex:
            print("Ok, got exception:", ex)


if __name__ == '__main__':
    main()
