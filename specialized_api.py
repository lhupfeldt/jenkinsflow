# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import json
from restkit import Resource, BasicAuth, errors


class UnknownJobException(Exception):
    def __init__(self, job_url):
        super(UnknownJobException, self).__init__("Job not found: " + job_url)


class ApiJob(object):
    def __init__(self, jenkins_resource, dct, name, parameter_definitions_dct, que_item_why):
        self.jenkins_resource = jenkins_resource
        self.dct = dct.copy()
        self.name = name
        self.parameter_definitions_dct = parameter_definitions_dct
        self.que_item_why = que_item_why

        self.build = None
        self.public_uri = self.baseurl = self.jenkins_resource.public_job_url(self.name)

        actions = self.dct.get('actions') or []
        for action in actions:
            if action.get('parameterDefinitions'):
                self.build_trigger_path = "/job/" + self.name + "/buildWithParameters"
                break
        else:
            self.build_trigger_path = "/job/" + self.name + "/build"

    def invoke(self, securitytoken, block, skip_if_running, invoke_pre_check_delay, invoke_block_delay, build_params, cause, files):
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
            self.jenkins_resource.post(self.build_trigger_path, **params)
        except errors.ResourceNotFound:
            raise UnknownJobException(self.jenkins_resource.public_job_url(self.name))

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

    def get_build_triggerurl(self):
        return self.jenkins_resource.public_uri + self.build_trigger_path

    def update_config(self, config_xml):
        self.jenkins_resource.post("/job/" + self.name + "/config.xml", payload=config_xml)

    def poll(self):
        pass

    def __repr__(self):
        return str(dict(name=self.name, dct=self.dct))


class ApiBuild(object):
    def __init__(self, job, dct):
        self.job = job
        self.dct = dct

    def is_running(self):
        return self.dct['building']

    def get_status(self):
        return self.dct['result']

    def get_result_url(self):
        return self.job.public_uri + '/' + str(self.buildno)

    @property
    def buildno(self):
        return self.dct['number']

    def __repr__(self):
        return self.job.name + " #" + repr(self.buildno)


class Jenkins(Resource):
    def __init__(self, direct_uri, job_prefix_filter=None, username=None, password=None, **kwargs):
        """
        direct_uri should be a non-proxied uri if possible (e.g. http://localhost:<port> if flow job is running on master)
        The public_uri will be retrieved from Jenkins and used in output
        """
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

    @baseurl.setter
    def baseurl(self, value):
        self._public_uri = self._baseurl = value

    @property
    def public_uri(self):
        if not self._public_uri:
            query = "primaryView[url]"
            response = self.get("/api/json", tree=query)
            dct = json.loads(response.body_string())
            print "dct:", dct
            self._public_uri = self._baseurl = dct['primaryView']['url'].rstrip('/')
        return self._public_uri

    @public_uri.setter
    def public_uri(self, value):
        self._public_uri = self._baseurl = value

    def public_job_url(self, job_name):
        return self.public_uri + '/job/' + job_name

    def _new_job(self, job_name, job_dct):
        que_item = job_dct.get('queueItem')
        que_item_why = que_item.get('why') if que_item else None

        parameter_definitions_dct = None
        actions = job_dct.get('actions') or []
        for action in actions:
            parameter_definitions_dct = action.get('parameterDefinitions')

        self.jobs[job_name] = ApiJob(self, job_dct, job_name, parameter_definitions_dct, que_item_why)

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
            self._new_job(job_name, job_dct)

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
                # A new job was created while flow was running
                self.job_poll(job_name)

    def job_poll(self, job_name):
        query = "lastBuild[number,building,result],inQueue,queueItem[why],actions[parameterDefinitions[name,type]]"
        response = self.get("/job/" + job_name + "/api/json", tree=query)
        job_dct = json.loads(response.body_string())
        job = self.jobs.get(job_name)
        if job:
            job.dct = job_dct
        else:
            self._new_job(job_name, job_dct)

    def get_job(self, name):
        try:
            return self.jobs[name]
        except KeyError:
            raise UnknownJobException(self.public_job_url(name))

    def create_job(self, job_name, config_xml):
        self.post('/createItem', name=job_name, headers={'Content-Type': 'application/xml header'}, payload=config_xml)

    def delete_job(self, job_name):
        try:
            self.post('/job/' + job_name + '/doDelete')
        except errors.ResourceNotFound:
            raise UnknownJobException(self.public_job_url(job_name))
