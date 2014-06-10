# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

import os, sys, importlib
from os.path import join as jp
import multiprocessing
from .api_base import UnknownJobException, ApiJobMixin, ApiBuildMixin

here = os.path.abspath(os.path.dirname(__file__))

def _mkdir(path):
    try:
        os.mkdir(path)
    except OSError:
        if not os.path.exists(path):
            raise


_build_res = None


def set_build_result(res):
    global _build_res
    _build_res = res


def _get_build_result():
    return _build_res


class LoggingProcess(multiprocessing.Process):
    def __init__(self, group=None, target=None, output_file_name=None, name=None, args=()):
        self.user_target = target
        super(LoggingProcess, self).__init__(group=group, target=self.run_job_wrapper, name=name, args=args)
        self.output_file_name = output_file_name

    def run_job_wrapper(self, *args):
        rc = 0
        set_build_result(None)
        try:
            rc = self.user_target(*args)
        except Exception as ex:  # pylint: disable=broad-except
            print("jenkinsflow.script_api: Caught exception from job script:", ex)
            rc = 1

        sbr = _get_build_result()
        print('sbr:', sbr)
        if sbr == None:
            sys.exit(rc)
        if sbr == 'unstable':
            sys.exit(2)
        print("jenkinsflow.script_api: Unknown requested build result:", sbr)
        sys.exit(1)

    def run(self):
        sys.stdout = sys.stderr = open(self.output_file_name, 'w', buffering=0)
        super(LoggingProcess, self).run()


class Jenkins(object):
    """Optimized minimal set of methods needed for jenkinsflow to directly execute python code instead of invoking Jenkins jobs.
    
    There is no concept of job queues or executors, so if your flow depends on these for correctness, you wil experience different behaviour
    when using this api instead of the real Jenkins.

    Args:
        direct_uri (str): Path to dir with 'job' method python modules. Modules named <job-name>.py will be imported from this directory.
            If no module exists for a specific jobname, the module called 'default.py' will be imported.
            The modules must contain at method called 'run_job' with the following signature:

                run_job(job_name, job_prefix_filter, username, password, securitytoken, cause, build_params)

                A return value of 0 is 'SUCCESS'
                A return value of 1 or any exception raised is 'FAILURE'
                Other return values means 'UNSTABLE'

        job_prefix_filter (str): Passed to 'run_job'. ``jenkinsflow`` puts no meaning into this parameter.
        securitytoken (str): Passed to 'run_job'. ``jenkinsflow`` puts no meaning into this parameter.
        username (str): Passed to 'run_job'. ``jenkinsflow`` puts no meaning into this parameter.
        job_prefix_filter (str): Passed to 'run_job'. ``jenkinsflow`` puts no meaning into this parameter.
        password (str): Passed to 'run_job'. ``jenkinsflow`` puts no meaning into this parameter.
        **kwargs: Ignored for compatibility with the other jenkins apis
    """

    def __init__(self, direct_uri, job_prefix_filter=None, username=None, password=None, log_dir='/tmp', **kwargs):
        self.job_prefix_filter = job_prefix_filter
        self.username = username
        self.password = password
        self.public_uri = self.baseurl = direct_uri
        self.log_dir = log_dir
        self.jobs = {}

    def poll(self):
        pass

    def quick_poll(self):
        pass

    def _script_file(self, job_name):
        return jp(self.public_uri, job_name + '.py')

    def get_job(self, name):
        job = self.jobs.get(name)
        if not job:
            script_file = script_file1 = self._script_file(name)
            if not os.path.exists(script_file):
                script_file = self._script_file('default')
                if not os.path.exists(script_file):
                    raise UnknownJobException(script_file1 + ' or ' + script_file)

            script_dir = os.path.dirname(script_file)
            if script_dir not in sys.path:
                sys.path.append(script_dir)

            try:
                user_module = importlib.import_module(os.path.basename(script_file).replace('.py', ''), package=None)
            except (ImportError, SyntaxError) as ex:
                raise UnknownJobException(repr(script_file) + ' ' + repr(ex))

            try:
                func = user_module.run_job
            except AttributeError as ex:
                raise UnknownJobException(script_file + repr(ex))

            job = self.jobs[name] = ApiJob(self, name, script_file, func)
        return job

    def create_job(self, job_name, config_xml):
        script_file = self._script_file(job_name)
        _mkdir(os.path.dirname(script_file))
        with open(script_file, 'w') as ff:
            ff.write(config_xml)

    def delete_job(self, job_name):
        script_file = self._script_file(job_name)
        try:
            os.unlink(script_file)
        except OSError as ex:
            if not os.path.exists(script_file):
                raise UnknownJobException(script_file + repr(ex))
            raise


class ApiJob(ApiJobMixin):
    def __init__(self, jenkins, name, script_file, func):
        self.jenkins = jenkins
        self.name = name

        self.build = None
        self.public_uri = self.baseurl = self.non_clickable_build_trigger_url = script_file
        self.func = func
        self.log_file = jp(self.jenkins.log_dir, self.name + '.log')
        self.build_num = 0

    def invoke(self, securitytoken, build_params, cause):
        _mkdir(self.jenkins.log_dir)
        self.build_num += 1
        fixed_args = [self.name, self.jenkins.job_prefix_filter, self.jenkins.username, self.jenkins.password, securitytoken, cause]
        fixed_args.append(build_params if build_params else {})
        proc = LoggingProcess(target=self.func, output_file_name=self.log_file, args=fixed_args)
        self.build = ApiBuild(self, proc, self.build_num)

    def is_running(self):
        build = self.get_last_build_or_none()
        return build.is_running() if build else False

    def is_queued(self):
        build = self.get_last_build_or_none()
        return (not build.is_running and build.proc.pid == None) if build else False

    def get_last_build_or_none(self):
        return self.build

    def update_config(self, config_xml):
        _mkdir(os.path.dirname(self.public_uri))
        with open(self.public_uri, 'w') as ff:
            ff.write(config_xml)

    def poll(self):
        pass

    def __repr__(self):
        return str(self.name)


class ApiBuild(ApiBuildMixin):
    def __init__(self, job, proc, buildno):
        self.job = job
        self.proc = proc
        self.buildno = buildno
        self.proc.start()

    def is_running(self):
        return self.proc.is_alive()

    def get_status(self):
        if self.is_running():
            return 'RUNNING'
        rc = self.proc.exitcode
        if rc == 0:
            return 'SUCCESS'
        if rc == 1:
            return 'FAILURE'
        return 'UNSTABLE'

    def __repr__(self):
        return self.job.name + " #" + repr(self.buildno)
