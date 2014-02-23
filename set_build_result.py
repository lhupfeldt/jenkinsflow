#!/usr/bin/python

# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

import argparse, os, tempfile

cli_jar = 'jenkins-cli.jar'

def set_build_result(username, password, result, java='java'):
    # Note: set-build-result can only be done from within the job
    # Note: only available if Jenkins URL set in Jenkins system configuration

    my_url = os.environ.get('BUILD_URL')
    if my_url is None:
        print("INFO: Not running inside Jenkins or Hudson job, no job to set result", repr(result), "for!")
        return

    base_url = os.environ.get('JENKINS_URL') or os.environ.get('HUDSON_URL')

    print("INFO: Setting job result to", repr(result))
    import urllib2, subprocess

    def set_res():
        command = [java, '-jar', cli_jar, '-s', my_url, 'set-build-result', result]
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
                except IOError:
                    pass
        else:
            subprocess.check_call(command)

    try:
        # If cli_jar is already present attempt to use it
        set_res()
    except subprocess.CalledProcessError :
        # We failed for some reason, try again with updated cli_jar
        cli_url = base_url + '/jnlpJars/' + cli_jar
        print("INFO: Downloading cli", repr(cli_url))
        response = urllib2.urlopen(cli_url)
        with open(cli_jar, 'w') as ff:
            ff.write(response.read())
        set_res()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Change result of JenkinsJob. Must be run from within the job!')
    parser.add_argument('--username', help='Name of jenkins user with access to the job')
    parser.add_argument('--password', help='Password of jenkins user with access to the job. *** Warning Insecure, will show up in process listing! ***')
    parser.add_argument('--result', default='unstable', help="The result to set. Should probably be 'unstable'")
    parser.add_argument('--java', default='java', help="Alternative 'java' executable.")
    args = parser.parse_args()

    set_build_result(args.username, args.password, args.result, args.java)
