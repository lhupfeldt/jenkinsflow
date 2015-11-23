# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

import click

from jenkinsflow.jenkins_api import Jenkins
from .utils import env_base_url


@click.command()
@click.option('--result', help="The result to set. Should probably be 'unstable'", default='unstable')
@click.option('--java', help="Alternative 'java' executable", default='java')
@click.option('--direct-url', help="Jenkins URL. Default is JENKINS_URL/HUDSON_URL env var value. Use this argument if JENKINS_URL is a proxy [default: None]")
@click.option('--username', help="Name of jenkins user with access to the job")
@click.option('--password', help="Password of jenkins user with access to the job.")
def set_build_result(username, password, result, direct_url=None, java='java'):
    """Change the result of a Jenkins job.

    Note: set_build_result can only be done from within the job, not after the job has finished.
    Note: Only available if URL is set in `Jenkins <http://jenkins-ci.org/>`_ system configuration.

    This command uses the Jenkins `cli` to change the result. It requires a java executable to run the Jenkins `cli`.
    Please note that in some versions of jenkins the cli is broken, it has no manifest file!
    """
    # %(file)s [--result <result>] [--java <java>] [--direct-url <direct_url>] [(--username <user_name> --password <password>)]

    if direct_url is not None:
        direct_url = direct_url + '/' if direct_url[-1] != '/' else direct_url
    jenkins = Jenkins(direct_url or env_base_url(), username=username, password=password)
    jenkins.set_build_result(result, java)
