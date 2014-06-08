# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import json
from restkit import Resource, BasicAuth, errors

from .api_base import UnknownJobException, ApiJobMixin, ApiBuildMixin


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
        query = "jobs[name,lastBuild[number,building,result],inQueue,queueItem[why],actions[parameterDefinitions[name,type]]],primaryView[url]"
        response = self.get("/api/json", tree=query)
        dct = json.loads(response.body_string())
        self._public_uri = self._baseurl = dct['primaryView']['url'].rstrip('/')

        self.jobs = {}
        for job_dct in dct.get('jobs') or []:
            job_name = str(job_dct['name'])
            if self.job_prefix_filter and not job_name.startswith(self.job_prefix_filter):
                continue
            self.jobs[job_name] = ApiJob(self, job_dct, job_name)

    def quick_poll(self):
        query = "jobs[name,lastBuild[number,building,result],inQueue]"
        response = self.get("/api/json", tree=query)
        dct = json.loads(response.body_string())

        for job_dct in dct.get('jobs') or []:
            job_name = str(job_dct['name'])
            if self.job_prefix_filter and not job_name.startswith(self.job_prefix_filter):
                continue
            job = self.jobs.get(job_name)
            if job:
                job.dct = job_dct
            else:
                # A new job was created while flow was running, get the remaining properties
                query = "lastBuild[number,building,result],inQueue,queueItem[why],actions[parameterDefinitions[name,type]]"
                response = self.get("/job/" + job_name + "/api/json", tree=query)
                job_dct = json.loads(response.body_string())
                self.jobs[job_name] = ApiJob(self, job_dct, job_name)

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
        except errors.ResourceNotFound:
            raise UnknownJobException(self._public_job_url(job_name))


class ApiJob(ApiJobMixin):
    def __init__(self, jenkins_resource, dct, name):
        self.jenkins_resource = jenkins_resource
        self.dct = dct.copy()
        self.name = name

        self.build = None
        self.public_uri = self.baseurl = self.jenkins_resource._public_job_url(self.name)  # pylint: disable=protected-access

        que_item = self.dct.get('queueItem')
        self.que_item_why = que_item.get('why') if que_item else None

        actions = self.dct.get('actions') or []
        for action in actions:
            if action.get('parameterDefinitions'):
                self._build_trigger_path = "/job/" + self.name + "/buildWithParameters"
                self.non_clickable_build_trigger_url = self.public_uri
                break
        else:
            self._build_trigger_path = "/job/" + self.name + "/build"
            self.non_clickable_build_trigger_url = self.public_uri

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
            self.jenkins_resource.post(self._build_trigger_path, **params)
        except errors.ResourceNotFound:
            raise UnknownJobException(self.jenkins_resource._public_job_url(self.name))  # pylint: disable=protected-access

    def is_running(self):
        build = self.get_last_build_or_none()
        return build.is_running() if build else False

    def is_queued(self):
        return self.dct['inQueue'] and not self.is_running()

    def get_last_build_or_none(self):
        bld_dct = self.dct.get('lastBuild')
        if bld_dct is None:
            return None
        if self.build:
            self.build.dct = bld_dct
            return self.build
        self.build = ApiBuild(self, bld_dct)
        return self.build

    def update_config(self, config_xml):
        self.jenkins_resource.post("/job/" + self.name + "/config.xml", payload=config_xml)

    def poll(self):
        pass

    def __repr__(self):
        return str(dict(name=self.name, dct=self.dct))


class ApiBuild(ApiBuildMixin):
    def __init__(self, job, dct):
        self.job = job
        self.dct = dct

    def is_running(self):
        return self.dct['building']

    def get_status(self):
        return self.dct['result']

    @property
    def buildno(self):
        return self.dct['number']

    def __repr__(self):
        return self.job.name + " #" + repr(self.buildno)
