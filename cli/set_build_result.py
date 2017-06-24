# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

import click

from ..jenkins_cli_protocol import CliProtocol
from ..utils import set_build_result as usbr


@click.command()
@click.option('--result', help="The result to set. Should probably be 'unstable'", default='unstable')
@click.option('--username', help="Name of jenkins user with access to the job")
@click.option('--password', help="Password of jenkins user with access to the job.")
@click.option('--java', help="Alternative 'java' executable", default='java')
@click.option('--direct-url', help="Jenkins URL. Default is JENKINS_URL/HUDSON_URL env var value. Use this argument if JENKINS_URL is a proxy [default: None]")
@click.option(
    '--protocol', default='remoting',
    help="The cli protocol to use. See https://jenkins.io/doc/book/managing/cli/. Only 'remoting' or unspecified is supported. [default: 'remoting'.]" \
    " Specify '' to not supply this option to the cli (for older Jenkins")
def set_build_result(result, username, password, direct_url, java, protocol):
    """Change the result of a Jenkins job.

    DEPRECATED - You should use shell step exit code to determine result.

    Note: set_build_result can only be done from within the job, not after the job has finished.
    Note: Only available if URL is set in `Jenkins <http://jenkins-ci.org/>`_ system configuration.

    This command uses the Jenkins `cli` to change the result. It requires a java executable to run the Jenkins `cli`.
    Please note that in some versions of jenkins the cli is broken, it has no manifest file!
    """
    # %(file)s [--result <result>] [--java <java>] [--direct-url <direct_url>] [(--username <user_name> --password <password>)]

    usbr.set_build_result(result, username, password, direct_url, java, CliProtocol[protocol] if protocol else None)
