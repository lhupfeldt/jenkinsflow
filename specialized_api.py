# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

import time, json
from restkit import Resource, BasicAuth, errors

from .api_base import BuildResult, Progress, UnknownJobException, ApiInvocationMixin


def _result_and_progress(build_dct):
    result = build_dct['result']
    progress = Progress.RUNNING if result is None else Progress.IDLE
    result = BuildResult.UNKNOWN if result is None else BuildResult[result]
    return (result, progress)


class Jenkins(Resource):
    """Optimized minimal set of methods needed for jenkinsflow to access Jenkins jobs.

    Args:
        direct_uri (str): Should be a non-proxied uri if possible (e.g. http://localhost:<port> if flow job is running on master)
            The public URI will be retrieved from Jenkins and used in output.
        job_prefix_filter (str): Jobs with names that don't start with this string, will be skpped when polling Jenkins.
            If you are using Hudson and have many jobs, it might be a good idea to enable Team support and create a job-runner user,
            which only has access to the jobs in the flow that it is executing. That way the job list will be filtered serverside.
        username (str): Name of user authorized to execute all jobs in flow.
        password (str): Password of user.
    """

    def __init__(self, direct_uri, job_prefix_filter=None, username=None, password=None, **kwargs):
        if username or password:
            if not (username and password):
                raise Exception("You must specify both username and password or neither")
            filters = kwargs.get('filters', [])
            filters.append(BasicAuth(username, password))
            kwargs['filters'] = filters
        super(Jenkins, self).__init__(direct_uri, **kwargs)
        self.direct_uri = direct_uri
        self.username = username
        self.password = password
        self.job_prefix_filter = job_prefix_filter
        self._public_uri = self._baseurl = None
        self.jobs = None
        self.queue_items = {}
        self.is_jenkins = True
        self.ci_version = None

    @property
    def baseurl(self):
        return self.public_uri

    @property
    def public_uri(self):
        if not self._public_uri:
            query = "primaryView[url]"
            response = self.get("/api/json", tree=query)
            dct = json.loads(response.body_string())
            self._public_uri = self._baseurl = dct['primaryView']['url'].rstrip('/')
        return self._public_uri

    def _public_job_url(self, job_name):
        return self.public_uri + '/job/' + job_name

    def poll(self):
        query = "jobs[name,lastBuild[number,result],queueItem[why],actions[parameterDefinitions[name,type]]],primaryView[url]"
        response = self.get("/api/json", tree=query)

        # Determine whether we are talking to Jenkins or Hudson
        self.ci_version = response.headers.get("X-Jenkins")
        if not self.ci_version:
            # TODO: A lot of Nonsense here because Hudson does not respond reliably
            head_response = "HEAD request failed: " + repr(self.direct_uri)
            for _ in (1, 2, 3):
                try:
                    head_response = self.head()
                    self.ci_version = head_response.headers.get("X-Hudson")
                    break
                except Exception:  # pragma: no cover
                    time.sleep(0.1)
            if not self.ci_version:
                raise Exception("Not connected to Jenkins or Hudson (expected X-Jenkins or X-Hudson header, got: " + repr(head_response.headers))
            self.is_jenkins = False

        dct = json.loads(response.body_string())
        self._public_uri = self._baseurl = dct['primaryView']['url'].rstrip('/')

        self.jobs = {}
        for job_dct in dct.get('jobs') or []:
            job_name = str(job_dct['name'])
            if self.job_prefix_filter and not job_name.startswith(self.job_prefix_filter):
                continue
            self.jobs[job_name] = ApiJob(self, job_dct, job_name)

    def quick_poll(self):
        query = "jobs[name,lastBuild[number,result],queueItem[why]]"
        response = self.get("/api/json", tree=query)
        dct = json.loads(response.body_string())

        for job_dct in dct.get('jobs') or []:
            job_name = str(job_dct['name'])
            if self.job_prefix_filter and not job_name.startswith(self.job_prefix_filter):
                continue
            job = self.jobs.get(job_name)
            if job:
                job.dct = job_dct
                continue

            # A new job was created while flow was running, get the remaining properties
            try:
                query = "lastBuild[number,result],queueItem[why],actions[parameterDefinitions[name,type]]"
                response = self.get("/job/" + job_name + "/api/json", tree=query)
                job_dct = json.loads(response.body_string())
                job = ApiJob(self, job_dct, job_name)
                self.jobs[job_name] = job
            except errors.ResourceNotFound:  # pragma: no cover
                # Ignore this, the job came and went
                pass

    def queue_poll(self):
        query = "items[task[name],id]"
        response = self.get("/queue/api/json", tree=query)
        dct = json.loads(response.body_string())

        queue_items = {}
        for qi_dct in dct.get('items') or []:
            job_name = str(qi_dct['task']['name'])
            if self.job_prefix_filter and not job_name.startswith(self.job_prefix_filter):
                continue

            queue_items.setdefault(job_name, []).append(qi_dct['id'])
        self.queue_items = queue_items

    def get_job(self, name):
        try:
            return self.jobs[name]
        except KeyError:
            raise UnknownJobException(self._public_job_url(name))

    def create_job(self, job_name, config_xml):
        self.post('/createItem', name=job_name, headers={'Content-Type': 'application/xml header'}, payload=config_xml)

    def delete_job(self, job_name):
        try:
            self.post('/job/' + job_name + '/doDelete')
        except errors.ResourceNotFound as ex:
            # TODO: Check error
            raise UnknownJobException(self._public_job_url(job_name), ex)


class ApiJob(object):
    def __init__(self, jenkins, dct, name):
        self.jenkins = jenkins
        self.dct = dct.copy()
        self.name = name
        self.public_uri = self.baseurl = self.jenkins._public_job_url(self.name)  # pylint: disable=protected-access

        actions = self.dct.get('actions') or []
        self._path = "/job/" + self.name
        for action in actions:
            if action.get('parameterDefinitions'):
                self._build_trigger_path = self._path + "/buildWithParameters"
                break
        else:
            self._build_trigger_path = self._path + "/build"
        self.old_build_number = None
        self.invocations = []
        self.queued_why = None

    def invoke(self, securitytoken, build_params, cause):
        try:
            params = {}
            if cause:
                build_params = build_params or {}
                build_params['cause'] = cause
            if build_params:
                params['headers'] = {'Content-Type': 'application/x-www-form-urlencoded'}
                params['payload'] = build_params
            if securitytoken:
                params['token'] = securitytoken
            response = self.jenkins.post(self._build_trigger_path, **params)
        except errors.ResourceNotFound as ex:
            raise UnknownJobException(self.jenkins._public_job_url(self.name), ex)  # pylint: disable=protected-access
        inv = Invocation(self, response.location[len(self.jenkins.direct_uri):] + 'api/json')
        self.invocations.append(inv)
        return inv

    def poll(self):
        for invocation in self.invocations:
            if not invocation.build_number:
                # Husdon does not return queue item from invoke, instead it returns the job URL :(
                query = "id,executable[number],why" if self.jenkins.is_jenkins else "queueItem[why,id],lastBuild[number]"
                qi_response = self.jenkins.get(invocation.queued_item_path, tree=query)
                dct = json.loads(qi_response.body_string())

                if self.jenkins.is_jenkins:
                    invocation.qid = dct.get('id')
                    executable = dct.get('executable')
                    if executable:
                        invocation.build_number = executable['number']
                        invocation.queued_why = None
                    else:
                        invocation.queued_why = dct['why']
                else:  # Hudson
                    # Note, this is not guaranteed to be correct in case of simultaneously running flows!
                    # Should handle multiple invocations in same flow
                    qi = dct.get('queueItem')
                    if qi:
                        invocation.qid = qi['id']
                        invocation.queued_why = qi['why']

                    last_build = dct.get('lastBuild')
                    if last_build:
                        last_build_number = last_build['number']
                        if last_build_number > self.old_build_number:
                            invocation.build_number = last_build['number']
                            self.old_build_number = invocation.build_number

    def job_status(self):
        """Result, progress and latest buildnumber info for the JOB NOT the invocation

        Return (result, progress_info, latest_build_number) (str, str, int or None):
            If there is no finished build, result will be BuildResult.UNKNOWN and latest_build_number will be None
        """
        progress = None

        query = "queueItem[why]"
        response = self.jenkins.get(self._path + '/api/json', tree=query)
        dct = json.loads(response.body_string())
        qi = dct['queueItem']
        if qi:
            progress = Progress.QUEUED
            self.queued_why = qi['why']

        dct = self.dct.get('lastBuild')
        if dct:
            self.old_build_number = dct['number']
            result, latest_progress = _result_and_progress(dct)
            return (result, progress or latest_progress, self.old_build_number)

        return (BuildResult.UNKNOWN, progress or Progress.IDLE, None)

    def stop_all(self):
        # First remove pending builds from queue
        queue_item_ids = self.jenkins.queue_items.get(self.name) or []
        for qid in queue_item_ids:
            try:
                self.jenkins.post('/queue/cancelItem?id=' + repr(qid))
            except errors.ResourceNotFound:
                # Job is no longer queued, so just ignore
                pass

        # Abort running builds
        query = "builds[number,result]"
        response = self.jenkins.get("/job/" + self.name + "/api/json", tree=query)
        dct = json.loads(response.body_string())
        for build in dct['builds']:
            _result, progress = _result_and_progress(build)
            if progress != Progress.IDLE:
                build_number = build['number']
                try:
                    self.jenkins.post(self._path + '/' + repr(build_number) + '/stop')
                except errors.ResourceNotFound:
                    # Job is no longer running, so just ignore
                    pass

    def update_config(self, config_xml):
        self.jenkins.post("/job/" + self.name + "/config.xml", payload=config_xml)

    def __repr__(self):
        return str(dict(name=self.name, dct=self.dct))


class Invocation(ApiInvocationMixin):
    def __init__(self, job, queued_item_path):
        self.job = job
        self.queued_item_path = queued_item_path
        self.qid = None
        self.build_number = None
        self.queued_why = None

    def status(self):
        """Result and Progress info for the invocation

        Return (result, progress_info) (str, str):
            If the build has not started or has not finished running, result will be BuildResult.UNKNOWN
        """

        if self.build_number is None:
            return (BuildResult.UNKNOWN, Progress.QUEUED)

        # It seems that even after the executor has been assigned a number in the queue item, the lastBuild might not yet exist
        dct = self.job.dct.get('lastBuild')
        last_number = dct['number'] if dct else None
        if last_number is None:
            return (BuildResult.UNKNOWN, Progress.QUEUED)

        if last_number == self.build_number:
            return _result_and_progress(dct)

        if last_number < self.build_number:
            # TODO: Why does this happen?
            pass  # pragma: no cover

        # Latest build is not ours, get the correct build
        query = "builds[number,result]"
        response = self.job.jenkins.get("/job/" + self.job.name + "/api/json", tree=query)
        dct = json.loads(response.body_string())
        for build in dct['builds']:
            if build['number'] == self.build_number:
                return _result_and_progress(build)

        raise Exception("Build deleted while flow running?")

    def stop(self):
        try:
            if self.build_number is not None:
                # Job has started
                self.job.jenkins.post(self.job._path + '/' + repr(self.build_number) + '/stop')
            else:
                # Job is queued
                self.job.jenkins.post('/queue/cancelItem?id=' + repr(self.qid))
        except errors.ResourceNotFound:
            # Job is no longer queued or running, so just ignore
            pass
