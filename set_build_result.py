#!/usr/bin/env python

# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

import sys, os, argparse, tempfile

jenkins_cli_jar = 'jenkins-cli.jar'
hudson_cli_jar = 'hudson-cli.jar'


def cli_jar_info(direct_url):
    base_url = os.environ.get('JENKINS_URL')
    cli_jar = jenkins_cli_jar

    if base_url is None:
        base_url = os.environ.get('HUDSON_URL')
        cli_jar = hudson_cli_jar

    return cli_jar, direct_url or base_url


def download_cli(cli_jar, base_url):
    import urllib2

    cli_url = base_url + '/jnlpJars/' + cli_jar
    print("INFO: Downloading cli:", repr(cli_url))
    response = urllib2.urlopen(cli_url)
    with open(cli_jar, 'w') as ff:
        ff.write(response.read())
    print("INFO: Download finished:", repr(cli_jar))


def set_build_result(username, password, result, direct_url=None, java='java'):
    """
    Note: set-build-result can only be done from within the job
    Note: only available if Jenkins URL set in Jenkins system configuration
    To use a URL different from JENKINS_URL (e.g. if Jenkins is behind a proxy) specify direct_url.
    """

    print("INFO: Setting job result to", repr(result))

    cli_jar, base_url = cli_jar_info(direct_url)
    if base_url is None:
        raise Exception("Could not get env variable JENKINS_URL or HUDSON_URL. Don't know whether to use " +
                        jenkins_cli_jar + " or " + hudson_cli_jar + " for setting result! " +
                        "You must set 'Jenkins Location' in Jenkins setup for JENKINS_URL to be exported. " +
                        "You must set 'Hudson URL' in Hudson setup for HUDSON_URL to be exported.")

    import subprocess

    def set_res():
        command = [java, '-jar', cli_jar, '-s', base_url, 'set-build-result', result]
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
    except subprocess.CalledProcessError :
        # We failed for some reason, try again with updated cli_jar
        download_cli(cli_jar, base_url)
        set_res()


def main(arguments):
    parser = argparse.ArgumentParser(description='Change result of a Jenkins Job. Must be run from within the job!')
    parser.add_argument('--username', help='Name of jenkins user with access to the job')
    parser.add_argument('--password', help='Password of jenkins user with access to the job. *** Warning Insecure, will show up in process listing! ***')
    parser.add_argument('--result', default='unstable', help="The result to set. Should probably be 'unstable'")
    parser.add_argument('--direct-url', default=None, help="Jenkins URL. Default is JENKINS_URL env var value. Use this argument if JENKINS_URL is a proxy.")
    parser.add_argument('--java', default='java', help="Alternative 'java' executable.")
    args = parser.parse_args(arguments)

    set_build_result(args.username, args.password, args.result, args.direct_url, args.java)


if __name__ == '__main__':
    main(sys.argv[1:])
