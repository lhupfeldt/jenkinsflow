# Copyright (c) 2012 - 2017 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

from .utils import base_url_and_api
from ..jenkins_cli_protocol import CliProtocol


def set_build_result(result, username, password, direct_url=None, java='java', protocol=CliProtocol.remoting):
    """Change the result of a Jenkins job.

    DEPRECATED - You should use the shell step exit code to determine the job result.

    Note: set_build_result can only be done from within the job, not after the job has finished.
    Note: Only available if URL is set in `Jenkins <http://jenkins-ci.org/>`_ system configuration.

    This command uses the Jenkins `cli` to change the result. It requires a java executable to run the Jenkins `cli`.
    Please note that in some versions of jenkins the cli is broken, it has no manifest file!

    Args:
        result (str): The result to set. Should probably be 'unstable'.
        username (str): Name of jenkins user with access to the job.
        password(str): Password of jenkins user with access to the job.
        direct-url (str): Jenkins URL. Default is JENKINS_URL/HUDSON_URL env var value. Use this argument if JENKINS_URL is a proxy.
        java (str): Alternative 'java' executable.
        protocol (CliProtocol): See https://jenkins.io/doc/book/managing/cli/.
    """

    base_url, api = base_url_and_api(direct_url)
    jenkins = api.Jenkins(base_url, username=username, password=password)
    jenkins.set_build_result(result, java, cli_call=True, protocol=protocol)
