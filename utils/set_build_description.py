# Copyright (c) 2012 - 2017 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

from .utils import base_url_and_api


def set_build_description(description, job_name=None, build_number=None, username=None, password=None, replace=False, separator='\n', direct_url=None):
    """Utility method to set/append build description on a job build.

    Args:
        job_name (str): Name of the job to modify a build on.
        build_number (int): Build Number to modify.
        description (str): The description to set on the build.
        username (str): User Name for Jenkin authentication with secured Jenkins.
        password (str): Password of Jenkins User.
        direct_url (str): Jenkins URL - preferably non-proxied. If not specified, the value of JENKINS_URL or HUDSON_URL environment variables will be used.
        replace (bool), default=False, help="Replace existing description, if any, instead of appending.")
        separator (str): A separator to insert between any existing description and the new 'description' if 'replace' is not specified.
    """

    base_url, api = base_url_and_api(direct_url)
    jenkins = api.Jenkins(direct_uri=base_url, username=username, password=password)
    jenkins.set_build_description(job_name, build_number, description, replace, separator)
