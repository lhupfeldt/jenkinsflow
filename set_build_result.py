# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function
import os, tempfile

from .utils import base_url_jenkins


jenkins_cli_jar = 'jenkins-cli.jar'
hudson_cli_jar = 'hudson-cli.jar'


def download_cli(cli_jar, direct_base_url, public_base_url):
    import urllib2
    
    path = '/jnlpJars/' + cli_jar
    if direct_base_url and direct_base_url != public_base_url:
        download_cli_url = direct_base_url + path
        print("INFO: Downloading cli:", repr(public_base_url + path), "(using direct url:", download_cli_url + ')')
    else:
        download_cli_url = public_base_url + path
        print("INFO: Downloading cli:", repr(download_cli_url))

    response = urllib2.urlopen(download_cli_url)
    with open(cli_jar, 'w') as ff:
        ff.write(response.read())
    print("INFO: Download finished:", repr(cli_jar))


def set_build_result(username, password, result, direct_url=None, java='java'):
    """Change the result of a Jenkins job.

    Note: set_build_result can only be done from within the job, not after the job has finished.
    Note: Only available if URL is set in `Jenkins <http://jenkins-ci.org/>`_ system configuration.

    This command uses the Jenkins `cli` to change the result. It requires a java executable to run the cli.

    Args:
        username (str): Name of jenkins user with access to the job
        password (str): Password of jenkins user with access to the job
        result (str): The result to set. Should probably be 'unstable'
        direct-url (str): Jenkins URL. Default is JENKINS_URL env var value. Use this argument if JENKINS_URL is a proxy.
        java (str): Alternative `java` executable. Use this if you don't wish to use the java in the PATH.
    """

    print("INFO: Setting job result to", repr(result))
    public_base_url, is_jenkins = base_url_jenkins()
    cli_jar = jenkins_cli_jar if is_jenkins else hudson_cli_jar

    if not public_base_url.startswith('http:'):
        # Using script_api
        from . import script_api
        script_api.set_build_result(result)
        return

    import subprocess32 as subprocess

    def set_res():
        command = [java, '-jar', cli_jar, '-s', direct_url if direct_url else public_base_url, 'set-build-result', result]
        if username or password:
            assert password and username, "You must specify both username and password if any"
            fname = None
            try:
                fhandle, fname = tempfile.mkstemp()
                fhandle = os.fdopen(fhandle, 'w')
                fhandle.write(password)
                fhandle.close()
                subprocess.check_call(command + ['--username', username, '--password-file', fname])
            finally:
                try:
                    os.remove(fname)
                    fhandle.close()
                except IOError:  # pragma: no cover
                    pass
        else:
            subprocess.check_call(command)

    try:
        # If cli_jar is already present attempt to use it
        set_res()
    except subprocess.CalledProcessError:
        # We failed for some reason, try again with updated cli_jar
        download_cli(cli_jar, direct_url, public_base_url)
        set_res()
