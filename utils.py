# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function
import os


def env_base_url():
    """Determines base_url when run from within a Jenkins/Hudson job
    
    Returns:
        base_url (str): If JENKINS_URL or HUDSON_URL is set, i.e. run from within job.

    Raises:
        Exception if neither JENKINS_URL nor HUDSON_URL is set, i.e. NOT run from within job.
    """

    base_url = os.environ.get('JENKINS_URL')
    if base_url:
        return base_url.rstrip('/')

    base_url = os.environ.get('HUDSON_URL')
    if base_url:
        return base_url.rstrip('/')

    if base_url is None:
        raise Exception("Could not get env variable JENKINS_URL or HUDSON_URL. "
                        "You must set 'Jenkins Location' in Jenkins setup for JENKINS_URL to be exported. "
                        "You must set 'Hudson URL' in Hudson setup for HUDSON_URL to be exported.")
