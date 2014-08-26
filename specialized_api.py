# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

import json, sys
from restkit import Resource, BasicAuth, errors

from .api_base import BuildResult, Progress, UnknownJobException, ApiInvocationMixin


def _debug(*args):
    print(*args)
    pass


def _json_dump(dct):
    if dct is None:
        print("dct is:", dct)
    json.dump(dct, sys.stdout, indent=2)
    print("")
    pass


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
        # _debug("\npoll")
        query = "jobs[name,lastBuild[number,result],inQueue,actions[parameterDefinitions[name,type]]],primaryView[url]"
        response = self.get("/api/json", tree=query)
        dct = json.loads(response.body_string())
        # _json_dump(dct)
        self._public_uri = self._baseurl = dct['primaryView']['url'].rstrip('/')

        self.jobs = {}
        for job_dct in dct.get('jobs') or []:
            job_name = str(job_dct['name'])
            if self.job_prefix_filter and not job_name.startswith(self.job_prefix_filter):
                continue
            self.jobs[job_name] = ApiJob(self, job_dct, job_name)

    def quick_poll(self):
        # _debug("\nquick_poll")
        query = "jobs[name,lastBuild[number,result],inQueue]"
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
                query = "lastBuild[number,result],inQueue,actions[parameterDefinitions[name,type]]"
                response = self.get("/job/" + job_name + "/api/json", tree=query)
                job_dct = json.loads(response.body_string())
                # _json_dump(job_dct)
                job = ApiJob(self, job_dct, job_name)
                self.jobs[job_name] = job
            except errors.ResourceNotFound:
                # Ignore this, the job came and went
                pass

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
        self.invocations = []

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
        # self.poll()
        return inv

    def poll(self):
        for invocation in self.invocations:
            # _debug("\njob.poll, queue_item")
            if not invocation.build_number:
                query = "executable[number],why"
                qi_response = self.jenkins.get(invocation.queued_item_path, tree=query)
                dct = json.loads(qi_response.body_string())

                executable = dct.get('executable')
                if executable:
                    invocation.build_number = executable['number']
                invocation.queued_why = dct['why']

    def job_status(self):
        """Result, progress and latest buildnumber info for the JOB NOT the invocation

        Return (result, progress_info, latest_build_number) (str, str, int or None):
            If there is no finished build, result will be BuildResult.UNKNOWN and latest_build_number will be None
        """

        query = "inQueue"
        response = self.jenkins.get(self._path + '/api/json', tree=query)
        dct = json.loads(response.body_string())
        _json_dump(dct)
        progress = Progress.QUEUED if dct['inQueue'] else None

        dct = self.dct.get('lastBuild')
        if dct:
            _debug("job.job_status")
            _json_dump(dct)
            result, latest_progress = _result_and_progress(dct)
            return (result, progress or latest_progress, dct['number'])

        return (BuildResult.UNKNOWN, progress or Progress.IDLE, None)

    def stop_latest(self):
        _result, progress, latest_build_number = self.job_status()
        if latest_build_number and progress != Progress.IDLE:
            self.jenkins.post(self._path + '/' + repr(latest_build_number) + '/stop')

    def update_config(self, config_xml):
        self.jenkins.post("/job/" + self.name + "/config.xml", payload=config_xml)

    def __repr__(self):
        return str(dict(name=self.name, dct=self.dct))


class Invocation(ApiInvocationMixin):
    def __init__(self, job, queued_item_path):
        # _debug("queued_item_path:", queued_item_path)
        self.job = job
        self.queued_item_path = queued_item_path
        self.build_number = None
        self.queued_why = None

    def status(self):
        """Result and Progress info for the invocation

        Return (result, progress_info) (str, str):
            If the build has not started or has not finished running, result will be BuildResult.UNKNOWN
        """

        if self.build_number is None:
            #_debug("status: no build_number", self.job.dct['inQueue'])
            # assert self.dct['inQueue']
            return (BuildResult.UNKNOWN, Progress.QUEUED)

        # It seems that even after the executor has been assigned a number in the queue item, the lastBuild migh not yet exist
        dct = self.job.dct.get('lastBuild')
        last_number = dct['number'] if dct else None
        #_json_dump(dct)
        if last_number is None:
            return (BuildResult.UNKNOWN, Progress.QUEUED)

        if last_number == self.build_number:
            return _result_and_progress(dct)

        if last_number < self.build_number:
            # TODO: Why does this happen?
            pass

        # Latest build is not ours, get the correct build
        query = "builds[number,result]"
        response = self.job.jenkins.get("/job/" + self.job.name + "/api/json", tree=query)
        dct = json.loads(response.body_string())
        #_json_dump(dct)
        for build in dct['builds']:
            if build['number'] == self.build_number:
                return _result_and_progress(build)

        raise Exception("Build deleted while flow running?")

    def stop(self):
        if self.build_number is not None:
            self.job.jenkins.post(self.job._path + '/' + repr(self.build_number) + '/stop')
