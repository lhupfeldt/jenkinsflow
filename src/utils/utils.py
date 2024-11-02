# Copyright (c) 2012 - 2024 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import sys
import os


def env_base_url():
    """Determines base_url when run from within a Jenkins job

    Returns:
        base_url (str): If JENKINS_URL is set, i.e. run from within job.

    Raises:
        Exception if JENKINS_URL is not set, i.e. NOT run from within job.
    """

    base_url = os.environ.get('JENKINS_URL')
    if base_url:
        return base_url.rstrip('/')

    if base_url is None:
        raise ValueError(
            "Could not get env variable JENKINS_URL. You must set 'Jenkins Location' in Jenkins setup for JENKINS_URL to be exported.")


def base_url_and_api(direct_url):
    try:
        base_url = direct_url.rstrip('/') if direct_url else env_base_url()
    except Exception:
        print("*** ERROR: You must specify 'direct-url' if not running from Jenkins job", file=sys.stderr)
        raise

    if base_url.startswith('http:') or base_url.startswith('https:'):
        # Using jenkins_api
        from ..jenkins_api import JenkinsApi as api
    else:
        # Using script_api
        from ..script_api import  ScriptApi as api

    return base_url, api
