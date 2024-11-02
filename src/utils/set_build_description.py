# Copyright (c) 2012 - 2017 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from .utils import base_url_and_api


def set_build_description(
        description: str, replace: bool = False, separator: str = '\n',
        username: str = None, password: str = None,
        build_url: str = None, job_name: str = None, build_number: int = None,
        direct_url: str = None):
    """Utility method to set/append build description on a job build.

    If this is used from inside the Jenkins job you do not have to specify 'build_url' or 'job_name', 'build_number'. You do not have to specify 'direct_url' either
    but may still want to do so if JENKINS_URL points to a proxy, so that rest calls can go directly to Jenkins.
    The 'build_url' is preferred over 'job_name' and 'build_number'.

    Args:
        description: The description to set on the build.
        replace: Replace existing description, if any, instead of appending.
        separator: A separator to insert between any existing description and the new 'description' if 'replace' is not specified.
        username: User Name for Jenkin authentication with secured Jenkins.
        password: Password of Jenkins User.
        build_url: The URL of the jenkins build - preferably non-proxied. Default is os.environ['BUILD_URL'].
        job_name: Name of the job to modify a build on. Default is os.environ['JOB_NAME'].
        build_number: Build Number to modify. . Default is os.environ['BUILD_NUMBER'].
        direct_url: Jenkins URL - preferably non-proxied. If not specified, the value of JENKINS_URL environment variables will be used.
    """

    base_url, api = base_url_and_api(direct_url)
    jenkins = api(direct_uri=base_url, username=username, password=password)
    jenkins.set_build_description(description, replace, separator, build_url, job_name, build_number)
