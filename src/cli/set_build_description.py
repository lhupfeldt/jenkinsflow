# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import click

from jenkinsflow.utils import set_build_description as usbd


@click.command()
@click.option('--description', help="The description to set on the build")
@click.option('--replace/--no-replace', default=False, help="Replace existing description, if any, instead of appending.")
@click.option('--separator', default='\n', help="A separator to insert between any existing description and the new 'description' if 'replace' is not specified.")
@click.option('--username', help="User Name for Jenkin authentication with secured Jenkins")
@click.option('--password', help="Password of Jenkins User")
@click.option('--build-url', help='Build URL', envvar='BUILD_URL')
@click.option('--job-name', help='Job Name', envvar='JOB_NAME')
@click.option('--build-number', help="Build Number", type=click.INT, envvar='BUILD_NUMBER')
@click.option(
    '--direct-url',
    default=None,
    help="Jenkins URL - preferably non-proxied. If not specified, the value of JENKINS_URL environment variables will be used.")
def set_build_description(description, replace, separator, username, password, build_url, job_name, build_number, direct_url):
    """Utility to set/append build description on a job build.

    When called from a Jenkins job you can leave out the '--build-url', '--job-name' and '--build-number' arguments, the BUILD_URL env variable will be used.
    """

    # %(file)s --job-name <job_name> --build-number <build_number> --description <description> [--direct-url <direct_url>] [--replace | --separator <separator>] [(--username <user_name> --password <password>)]

    usbd.set_build_description(description, replace, separator, username, password, build_url, job_name, build_number, direct_url)
