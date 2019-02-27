# Copyright (c) 2012 - 2017 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from .utils import base_url_and_api


def set_build_description(description, replace=False, separator='\n', username=None, password=None, job_name=None, build_number=None, direct_url=None):
    """Utility method to set/append build description on a job build.

    If this is used from inside the hudson job you do not have to specify 'job_name', 'build_number' and 'direct_url'.

    Args:
        description (str): The description to set on the build.
        replace (bool): Replace existing description, if any, instead of appending.
        separator (str): A separator to insert between any existing description and the new 'description' if 'replace' is not specified.
        username (str): User Name for Jenkin authentication with secured Jenkins.
        password (str): Password of Jenkins User.
        job_name (str): Name of the job to modify a build on. Default is os.environ['JOB_NAME'].
        build_number (int): Build Number to modify. . Default is os.environ['BUILD_NUMBER'].
        direct_url (str): Jenkins URL - preferably non-proxied. If not specified, the value of JENKINS_URL or HUDSON_URL environment variables will be used.
    """

    base_url, api = base_url_and_api(direct_url)
    jenkins = api.Jenkins(direct_uri=base_url, username=username, password=password)
    jenkins.set_build_description(description, replace, separator, job_name, build_number)
