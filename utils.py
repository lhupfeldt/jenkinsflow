# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function
import os


def base_url_jenkins():
    """Determines base_url when run from within a Jenkins/Hudson job
    
    Return
        base_url if run from within job else None, True if Jenkins else False
    """

    base_url = os.environ.get('JENKINS_URL')
    if base_url:
        return base_url.rstrip('/'), True

    base_url = os.environ.get('HUDSON_URL')
    if base_url:
        return base_url.rstrip('/'), False

    if base_url is None:
        raise Exception("Could not get env variable JENKINS_URL or HUDSON_URL. "
                        "You must set 'Jenkins Location' in Jenkins setup for JENKINS_URL to be exported. "
                        "You must set 'Hudson URL' in Hudson setup for HUDSON_URL to be exported.")
