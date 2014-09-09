#!/usr/bin/env python

# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

"""
Utility to set/append build description on a job build.

Usage:
%(file)s --direct-url <direct_url> --job-name <job_name> --build-number <build_number> --description <description> [--append [--separator <separator>]] [(--username <user_name> --password <password>)]

-u, --direct-url <direct_url>      Jenkins URL - possibly non-proxied
-j, --job-name <job_name>          Job Name
-b, --build-number <build_number>  Build Number
-d, --description <description>    The description to set on the build

-a, --append                       If True append to existing description, if any. [default: true]
-s, --separator <separator>        A separator to insert between any existing description and the new 'description'
                                   if 'append' is true. [default: \\n]

--username <user_name>             User Name for Jenkin authentication with secured Jenkins
--password <password>              Password of Jenkins User
"""


from __future__ import print_function
from docopt import docopt


def set_build_description(jenkins, job_name, build_number, description, append=True, separator='\n'):
    """Utility to set/append build description
    Args
        jenkins (Jenkins),
        job_name (str)
        build_number (int)
        description (str): The description to set on the build
        append (bool):     If True append to existing description, if any
        separator (str):   A separator to insert between any existing description and the new :py:obj:`description` if :py:obj:`append` is True.
    """
    jenkins.set_build_description(job_name, build_number, description, append, separator)


def main():
    doc = __doc__ % dict(file=__file__)
    args = docopt(doc, argv=None, help=True, version=None, options_first=False)

    direct_url = args['--direct-url']
    job_name = args['--job-name']
    build_number = args['--build-number']
    description = args['--description']
    append = args['--append']
    separator = '\n' if str(args['--separator']) == '\\n' else args['--separator']
    username = args['--username']
    password = args['--password']

    print("direct_url",     direct_url)
    print("job_name",     job_name)
    print("build_number",     build_number)
    print("description",     description)
    print("append",     append)
    print("separator",     separator)
    print("username",     username)
    print("password",     password)

    if direct_url.startswith('http:'):
        # Using specialized_api
        from . import specialized_api as api
    else:
        # Using script_api
        from . import script_api as api

    jenkins = api.Jenkins(direct_uri=direct_url, username=username, password=password)
    set_build_description(jenkins, job_name, build_number, description, append, separator)


# Allow relative imports while running as script
if __name__ == "__main__" and __package__ is None:
    import sys, os
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(1, os.path.dirname(here))
    import jenkinsflow
    __package__ = "jenkinsflow"
    del sys, os
    main()
