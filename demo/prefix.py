#!/usr/bin/env python3

# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from jenkinsflow.flow import serial

import lib.demo_security as security


def main(api):
    with serial(api, timeout=70, report_interval=3, job_name_prefix='jenkinsflow_demo__prefix__') as ctrl1:
        ctrl1.invoke('quick1')

        for index in 1, 2, 3:
            with ctrl1.serial(timeout=20, report_interval=3, job_name_prefix='x_') as ctrl2:
                ctrl2.invoke('quick2-' + str(index))

        ctrl1.invoke('quick3')

        with ctrl1.parallel(timeout=40, report_interval=3, job_name_prefix='y_') as ctrl2:
            with ctrl2.serial(timeout=40, report_interval=3, job_name_prefix='z_') as ctrl3:
                ctrl3.invoke('quick4')

            ctrl2.invoke('quick5')


if __name__ == '__main__':
    # Note: This flow uses username/password instead of securitytoken, to demonstrate that feature, it could have used securitytoken.
    # See demo_security.py
    import os
    from jenkinsflow.jenkins_api import JenkinsApi
    jenkins = JenkinsApi(os.environ.get('JENKINS_URL') or "http://localhost:8080", username=security.username, password=security.password)
    main(jenkins)
