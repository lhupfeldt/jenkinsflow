#!/usr/bin/env python3

# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from jenkinsflow.flow import serial

import demo_security as security


def main(api):
    with serial(api, timeout=70, securitytoken=security.securitytoken, job_name_prefix='jenkinsflow_demo__hide_password__', report_interval=3, secret_params='.*PASS.*|.*pass.*') as ctrl:
        # NOTE: In order to ensure that passwords are not displayed in a stacktrace you must never put a literal password
        # In the last line in the with statement, or in any statement that may raise an exception. You shold not really
        # put clear text paswords in you code anyway :)
        p1, p2, p3 = 'SECRET', 'sec', 'not_security'
        ctrl.invoke('passwd_args', password=p1, s1='no-secret', passwd=p2, PASS=p3)


if __name__ == '__main__':
    import os
    from jenkinsflow.jenkins_api import Jenkins
    url = os.environ.get('JENKINS_URL') or os.environ.get('HUDSON_URL') or "http://localhost:8080"
    main(Jenkins(url, username=security.username, password=security.password) if security.default_use_login else Jenkins(url))
