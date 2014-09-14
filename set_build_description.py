#!/usr/bin/env python

# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

"""
Utility to set/append build description on a job build.

Usage:
%(file)s --job-name <job_name> --build-number <build_number> --description <description> [--direct-url <direct_url>] [--replace | --separator <separator>] [(--username <user_name> --password <password>)]

-j, --job-name <job_name>          Job Name
-b, --build-number <build_number>  Build Number
-d, --description <description>    The description to set on the build

--direct-url <direct_url>          Jenkins URL - preferably non-proxied.
                                   If not specified, the value of JENKINS_URL or HUDSON_URL environment variables will be used.

-r, --replace                      If specified replace existing description, if any. [default: false]
-s, --separator <separator>        A separator to insert between any existing description and the new 'description'
                                   if 'replace' is not specified. [default: \\n]

--username <user_name>             User Name for Jenkin authentication with secured Jenkins
--password <password>              Password of Jenkins User
"""


from __future__ import print_function
import sys, os
from docopt import docopt

# Allow relative imports while running as script
if __package__ is None:
    _here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(1, os.path.dirname(_here))
    import jenkinsflow
    __package__ = "jenkinsflow"

from .utils import base_url_jenkins


def set_build_description(jenkins, job_name, build_number, description, replace=False, separator='\n'):
    """Utility to set/append build description
    Args
        jenkins (Jenkins):  A :py:class:`.jenkins_api.Jenkins` instance  
        job_name (str)      The job for which to set description on a build
        build_number (int): The build to set description on
        description (str):  The description to set on the build
        replace (bool):     If True, replace existing description, if any, instead of appending to it
        separator (str):    A separator to insert between any existing description and the new :py:obj:`description` if :py:obj:`replace` is False.
    """
    jenkins.set_build_description(job_name, build_number, description, replace, separator)


def main(arguments):
    doc = __doc__ % dict(file=os.path.basename(__file__))
    args = docopt(doc, argv=arguments, help=True, version=None, options_first=False)

    base_url = args['--direct-url']
    job_name = args['--job-name']
    build_number = args['--build-number']
    description = args['--description']
    replace = args['--replace']
    separator = '\n' if str(args['--separator']) == '\\n' else args['--separator']
    username = args['--username']
    password = args['--password']
 
    if not base_url:
        try:
            base_url, _ = base_url_jenkins()
        except Exception:
            print("*** ERROR: You must specify '--direct-url' if not running from Jenkins job", file=sys.stderr)
            raise

    if base_url.startswith('http:'):
        # Using jenkins_api
        from . import jenkins_api as api
    else:
        # Using script_api
        from . import script_api as api

    jenkins = api.Jenkins(direct_uri=base_url, username=username, password=password)
    set_build_description(jenkins, job_name, build_number, description, not replace, separator)


if __name__ == "__main__":
    main(sys.argv[1:])
