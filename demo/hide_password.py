#!/usr/bin/env python3

# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from jenkinsflow.flow import serial

import lib.get_jenkins_api


def main(api, securitytoken):
    with serial(api, timeout=70, securitytoken=securitytoken, job_name_prefix='jenkinsflow_demo__hide_password__', report_interval=3, secret_params='.*PASS.*|.*pass.*') as ctrl:
        # NOTE: In order to ensure that passwords are not displayed in a stacktrace you must never put a literal password
        # In the last line in the with statement, or in any statement that may raise an exception. You shold not really
        # put clear text paswords in you code anyway :)
        p1, p2, p3 = 'SECRET', 'sec', 'not_security'
        ctrl.invoke('passwd_args', password=p1, s1='no-secret', passwd=p2, PASS=p3)


if __name__ == '__main__':
    main(*lib.get_jenkins_api.get_jenkins_api())
