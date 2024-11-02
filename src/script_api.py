# Copyright (c) 2012 - 2024 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import sys
import os
from os.path import join as jp
import shutil
import importlib
import datetime
import tempfile
import urllib.parse

import psutil

from .api_base import BuildResult, Progress, UnknownJobException, BaseApiMixin, ApiInvocationMixin
from .speed import Speed
from .logging_process import LoggingProcess


def _pgrep(proc_name):
    """Returns True if a process with name 'proc_name' is running, else False"""
    for proc in psutil.process_iter():
        try:
            if proc.name() == proc_name:
                return True
        except psutil.NoSuchProcess:
            # May happen if proc disappears during iteration
            continue

    return False


class ScriptApi(Speed, BaseApiMixin):
    """Optimized minimal set of methods needed for jenkinsflow to directly execute python code instead of invoking Jenkins jobs.

    THIS DOES NOT SUPPORT CONCURRENT INVOCATIONS OF FLOW

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
        username (str): Passed to 'run_job'. ``jenkinsflow`` puts no meaning into this parameter.
        password (str): Passed to 'run_job'. ``jenkinsflow`` puts no meaning into this parameter.
        invocation_class (class): Defaults to `Invocation`.
        log_dir (str): Directory in which to store logs. Defaults to subdirectory 'jenkinsflow' under the system defined tmp dir.
        **kwargs: Ignored for compatibility with the other jenkins apis
    """

    def __init__(self, direct_uri, job_prefix_filter=None, username=None, password=None, invocation_class=None, log_dir=None, **kwargs):
        self.job_prefix_filter = job_prefix_filter
        self.username = username
        self.password = password
        self.public_uri = direct_uri
        self.log_dir = log_dir or os.path.join(tempfile.gettempdir(), 'jenkinsflow')
        self.invocation_class = invocation_class or Invocation
        self.jenkins_prefix = urllib.parse.urlsplit(direct_uri).path  # If direct_uri is a path, then jenkins_prefix will be the same as direct_uri
        self.jobs = {}

    def poll(self):
        pass

    def quick_poll(self):
        pass

    def queue_poll(self):
        pass

    def _script_file(self, job_name):
        return jp(self.public_uri, job_name + '.py')

    def _workspace(self, job_name):
        return jp(self.public_uri, job_name.replace('/', '_'))

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
                raise UnknownJobException(repr(script_file) + ' ' + repr(ex)) from ex

            try:
                func = user_module.run_job
            except AttributeError as ex:
                raise UnknownJobException(script_file + repr(ex)) from ex
            job = self.jobs[name] = ApiJob(jenkins=self, name=name, script_file=script_file, workspace=self._workspace(name), func=func)
        return job

    def create_job(self, job_name, config_xml):
        script_file = self._script_file(job_name)
        os.makedirs(os.path.dirname(script_file), exist_ok=True)
        with open(script_file, 'w', encoding="utf-8") as ff:
            ff.write(config_xml)

    def delete_job(self, job_name):
        script_file = self._script_file(job_name)
        try:
            os.unlink(script_file)
        except OSError as ex:
            if not os.path.exists(script_file):
                raise UnknownJobException(script_file + repr(ex)) from ex
            raise

        try:
            shutil.rmtree(self._workspace(job_name))
        except OSError as ex:
            if os.path.exists(script_file):
                raise

    def set_build_description(
            self, description: str, replace: bool = False, separator: str = '\n',
            build_url: str = None, job_name: str = None, build_number: int = None):
        """Utility to set/append build description. :py:obj:`description` will be written to a file in the workspace.

        Args:
            description: The description to set on the build.
            append:      If True append to existing description, if any.
            separator:   A separator to insert between any existing description and the new :py:obj:`description` if :py:obj:`append` is True.
            build_url:
            job_name:
            build_number:
        """

        rel_build_url = self.get_build_url(build_url, job_name, build_number)
        # TODO: Is this always correct?
        workspace = self._workspace(os.path.basename(os.path.dirname(rel_build_url).replace('.py', '')))
        mode = 'w' if replace else 'a'
        fname = jp(workspace, 'description.txt')
        if not replace and os.path.exists(fname) and os.stat(fname).st_size:
            description = separator + description
        with open(fname, mode, encoding="utf-8") as ff:
            try:
                ff.write(description)
            except UnicodeEncodeError:
                ff.write(description.encode('utf-8'))


class ApiJob():
    def __init__(self, jenkins, name, script_file, workspace, func):
        self.jenkins = jenkins
        self.name = name

        self.build = None
        self.public_uri = script_file
        self.workspace = workspace
        self.func = func
        self.log_file = jp(self.jenkins.log_dir, self.name + '.log')
        self.build_num = None
        self._invocations = []
        self.queued_why = None
        self.old_build_number = None

    def invoke(self, securitytoken, build_params, cause, description):
        os.makedirs(self.jenkins.log_dir, exist_ok=True)
        os.makedirs(self.workspace, exist_ok=True)
        build_number = (self.build_num or 0) + 1
        self.build_num = build_number

        fixed_args = [self.name, self.jenkins.job_prefix_filter, self.jenkins.username, self.jenkins.password, securitytoken, cause]
        fixed_args.append(build_params if build_params else {})

        # Export some of the same variables that Jenkins does
        extra_env = dict(
            BUILD_NUMBER=repr(build_number),
            BUILD_ID=datetime.datetime.isoformat(datetime.datetime.utcnow()),
            BUILD_DISPLAY_NAME='#' + repr(build_number),
            JOB_NAME=self.name,
            BUILD_TAG='jenkinsflow-' + self.name + '-' + repr(build_number),
            NODE_NAME='built-in',
            NODE_LABELS='',
            WORKSPACE=self.workspace,
            JENKINS_HOME=self.jenkins.public_uri,
            JENKINS_URL=self.jenkins.public_uri,
            BUILD_URL=jp(self.public_uri, repr(build_number)),
            JOB_URL=self.public_uri,
        )

        proc = LoggingProcess(target=self.func, output_file_name=self.log_file, workspace=self.workspace, name=self.name, args=fixed_args, env=extra_env)
        self.build = self.jenkins.invocation_class(self, proc, build_number)
        if description:
            self.jenkins.set_build_description(description, replace=True, separator='', job_name=self.name, build_number=build_number)
        self._invocations.append(self.build)
        return self.build

    def poll(self):
        pass

    def job_status(self):
        """Result, progress and latest buildnumber info for the JOB NOT the invocation

        Return (result, progress_info, latest_build_number) (str, str, int or None):
            Note: Always returns result == BuildResult.UNKNOWN and latest_build_number == 0
        """

        progress = Progress.RUNNING if _pgrep(LoggingProcess.proc_name_prefix + self.name) else Progress.IDLE
        result = BuildResult.UNKNOWN
        return (result, progress, 0)

    def stop_all(self):
        # TODO stop ALL
        if self.build:
            self.build.proc.terminate()

    def update_config(self, config_xml):
        os.makedirs(os.path.dirname(self.public_uri), exist_ok=True)
        with open(self.public_uri, 'w', encoding="utf-8") as ff:
            ff.write(config_xml)

    def __repr__(self):
        return str(self.name)


class Invocation(ApiInvocationMixin):
    def __init__(self, job, proc, build_number):
        self.job = job
        self.proc = proc
        self.build_number = build_number
        self.queued_why = None

        self.proc.start()

    def status(self):
        if self.proc.is_alive():
            return (BuildResult.UNKNOWN, Progress.RUNNING)
        rc = self.proc.exitcode
        if rc == 0:
            return (BuildResult.SUCCESS, Progress.IDLE)
        if rc == 1:
            return (BuildResult.FAILURE, Progress.IDLE)
        return (BuildResult.UNSTABLE, Progress.IDLE)

    def stop(self, dequeue):  # pylint: disable=unused-argument
        self.proc.terminate()

    def console_url(self):
        return self.job.log_file

    def __repr__(self):
        return self.job.name + " #" + repr(self.build_number)
