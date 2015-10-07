# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function
import sys

import click

from .utils import env_base_url


@click.command()
@click.option('--job-name', help='Job Name', envvar='JOB_NAME')
@click.option('--build-number', help="Build Number", type=click.INT)
@click.option('--description', help="The description to set on the build")
@click.option(
    '--direct-url',
    default=None,
    help="Jenkins URL - preferably non-proxied. If not specified, the value of JENKINS_URL or HUDSON_URL environment variables will be used.")
@click.option('--replace/--no-replace', default=False, help="Replace existing description, if any, instead of appending.")
@click.option('--separator', default='\n', help="A separator to insert between any existing description and the new 'description' if 'replace' is not specified.")
@click.option('--username', help="User Name for Jenkin authentication with secured Jenkins")
@click.option('--password', help="Password of Jenkins User")
def set_build_description(job_name, build_number, description, replace, separator, direct_url, username, password):
    """Utility to set/append build description on a job build."""
    # %(file)s --job-name <job_name> --build-number <build_number> --description <description> [--direct-url <direct_url>] [--replace | --separator <separator>] [(--username <user_name> --password <password>)]

    base_url = direct_url
    if not base_url:
        try:
            base_url = env_base_url()
        except Exception:
            print("*** ERROR: You must specify '--direct-url' if not running from Jenkins job", file=sys.stderr)
            raise

    if base_url.startswith('http:'):
        # Using jenkins_api
        from .. import jenkins_api as api
    else:
        # Using script_api
        from .. import script_api as api

    jenkins = api.Jenkins(direct_uri=base_url, username=username, password=password)
    jenkins.set_build_description(job_name, build_number, description, replace, separator)
