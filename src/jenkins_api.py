# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import os
import os.path
import time
from collections import OrderedDict
import urllib.parse
# import json

from .api_base import BuildResult, Progress, ClientError, UnknownJobException, BaseApiMixin, ApiInvocationMixin
from .speed import Speed
from .rest_api_wrapper import ResourceNotFound, RequestsRestApi


_SUPERSEDED_PSEUDO_BUILD_NUM = -1
_DEQUEUED_PSEUDO_BUILD_NUM = -2

_CT_URL_ENC = {'Content-Type': 'application/x-www-form-urlencoded'}


# Quick poll query to get state after starting job,
_QUICK_QUERY = "jobs[name,lastBuild[number,result],queueItem[why]]"

# Query info and parameter definitions of a specific job
_GIVEN_JOB_QUERY_WITH_PARAM_DEFS = "lastBuild[number,result],queueItem[why],actions[parameterDefinitions[name,type]],property[parameterDefinitions[name,type]]"

# Initial query
# Build a three level query to handle github organization folder jobs.
# Note that 'name' in response does not contain first 'job/' from url, but does contain intermediate 'job/', so:
# 'name': 'gh-org/job/jenkinsflow-gh-folder-test/job/main'
# Corresponds:
# 'url': 'http://<host>:<port>/job/gh-org/job/jenkinsflow-gh-folder-test/job/main'
_ONE_LEVEL_JOBS_INFO_QUERY = f"jobs[name,{_GIVEN_JOB_QUERY_WITH_PARAM_DEFS}_RECURSE_]"
_TWO_LEVELS_JOBS_INFO_QUERY = _ONE_LEVEL_JOBS_INFO_QUERY.replace("_RECURSE_", "," + _ONE_LEVEL_JOBS_INFO_QUERY)
_THREE_LEVELS_JOBS_INFO_QUERY = _TWO_LEVELS_JOBS_INFO_QUERY.replace("_RECURSE_", "," + _ONE_LEVEL_JOBS_INFO_QUERY)
_FULL_QUERY = f"{_THREE_LEVELS_JOBS_INFO_QUERY.replace('_RECURSE_', '')},primaryView[url]"


def _result_and_progress(build_dct):
    result = build_dct['result']
    progress = Progress.RUNNING if result is None else Progress.IDLE
    result = BuildResult.UNKNOWN if result is None else BuildResult[result]
    return (result, progress)


class JenkinsApi(Speed, BaseApiMixin):
    """Optimized minimal set of methods needed for jenkinsflow to access Jenkins jobs.

    Args:
        direct_uri (str): Should be a non-proxied uri if possible (e.g. http://localhost:<port> if flow job is running on 'built-in' node)
            The public URI will be retrieved from Jenkins and used in output.
        job_prefix_filter (str): Jobs with names that don't start with this string, will be skpped when polling Jenkins.
        username (str): Name of user authorized to execute all jobs in flow.
        password (str): Password of user.
        invocation_class (class): Defaults to `Invocation`. You can subclass that to provide your own class.
        csrf (bool): Will attempt to get (and use) a CSRF protection crumb from Jenkins. A 404 - ResourceNotFound error is silently
            ignored as this indicates that csrf protection is not enabled on Jenkins.
    """

    def __init__(self, direct_uri, job_prefix_filter=None, username=None, password=None, invocation_class=None, rest_access_provider=RequestsRestApi, csrf=True):
        if username or password:
            if not (username and password):
                raise ValueError("You must specify both username and password or neither")
        self.rest_api = rest_access_provider(direct_uri, username, password)

        self.direct_uri = direct_uri
        self.username = username
        self.password = password
        self.invocation_class = invocation_class or Invocation
        self.job_prefix_filter = job_prefix_filter
        self.jenkins_prefix = urllib.parse.urlsplit(direct_uri).path  # When jenkins is started with a 'prefix' value
        self._public_uri = None
        self.jobs = None
        self.queue_items = {}
        self.is_jenkins = False
        self.csrf = csrf
        self._crumb = None

    def _get_fresh_crumb(self):
        """Get the CSRF crumb to be put on subsequent requests"""
        try:
            crumb = self.rest_api.get_content('/crumbIssuer/api/xml', xpath='concat(//crumbRequestField,":",//crumb)').split(b':')
            self._crumb = {crumb[0]: crumb[1]}
        except ResourceNotFound:
            self.csrf = False

    def get_json(self, url="", **params):  # pylint: disable=inconsistent-return-statements
        # Sometimes (but rarely) Jenkins will Abort the connection when jobs are being aborted!
        for ii in (1, 2, 3):
            try:
                return self.rest_api.get_json(url, **params)
            except ConnectionError as ex:
                if ii == 3:
                    raise
                print("WARNING: Retrying failed 'poll':", ex)
                time.sleep(0.1)

    def post(self, url, payload=None, headers=None, **params):  # pylint: disable=inconsistent-return-statements
        for crumb_attempt in (0, 1):
            if self._crumb:
                if headers:
                    headers = headers.copy()
                    headers.update(self._crumb)
                else:
                    headers = self._crumb

            try:
                return self.rest_api.post(url, payload, headers, **params)
            except ClientError as ex:
                if crumb_attempt:
                    raise
                if self.csrf:
                    if self._crumb:
                        print("INFO: getting new crumb:", ex)
                    self._get_fresh_crumb()

    def headers(self):
        return self.rest_api.headers()

    @property
    def public_uri(self):
        if not self._public_uri:
            query = "primaryView[url]"
            dct = self.get_json(tree=query)
            self._public_uri = dct['primaryView']['url'].rstrip('/')
        return self._public_uri

    def _public_job_url(self, job_name):
        return self.public_uri + '/job/' + job_name

    def _resolve_job_levels(self, dct, parent_job_name):
        """Resolve jobs for a poll. E.g. gh folder jobs have three levels <org>/<repo>/<branch>."""
        has_children = False
        for job_dct in dct.get('jobs') or []:
            has_children = True

            # print("poll - job_dct:", json.dumps(job_dct, indent=2))
            job_name = str(job_dct['name'])
            # print("job_name:", job_name)

            if self.job_prefix_filter and not job_name.startswith(self.job_prefix_filter):
                continue

            if parent_job_name:
                job_name = f"{parent_job_name}/job/{job_name}"
            # print("full job_name:", job_name)
            # print(json.dumps(job_dct, indent=2))
            has_grand_children = self._resolve_job_levels(job_dct, job_name)
            self.jobs[job_name] = ApiJob(self, job_dct, job_name, has_grand_children)


            #if job_dct["_class"] not in ("hudson.model.FreeStyleProject", "org.jenkinsci.plugins.workflow.job.WorkflowJob"):
            #    print(json.dumps(self.get_json(depth=3), indent=2))

        return has_children

    def poll(self):
        if not self.is_jenkins:
            # Determine whether we are talking to Jenkins
            head_response = self.headers()
            if head_response.get("X-Jenkins"):
                self.is_jenkins = True
            else:
                raise Exception("Not connected to Jenkins. Expected X-Jenkins header, got: " + repr(head_response))

        dct = self.get_json(tree=_FULL_QUERY)
        self._public_uri = dct['primaryView']['url'].rstrip('/')

        self.jobs = {}
        self._resolve_job_levels(dct, None)

    def quick_poll(self):
        dct = self.get_json(tree=_QUICK_QUERY)
        # print("dct:", json.dumps(dct, indent=2))

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
                job_dct = self.get_json("/job/" + job_name, tree=_GIVEN_JOB_QUERY_WITH_PARAM_DEFS)
                # print("new job:", job_dct)
                job = ApiJob(self, job_dct, job_name, has_children=False)  # TODO _resolve...
                self.jobs[job_name] = job
            except ResourceNotFound:  # pragma: no cover
                # Ignore this, the job came and went
                pass

    def queue_poll(self):
        query = "items[task[name],id]"
        dct = self.get_json("/queue", tree=query)

        queue_items = {}
        for qi_dct in dct.get('items') or []:
            job_name = str(qi_dct['task']['name'])
            if self.job_prefix_filter and not job_name.startswith(self.job_prefix_filter):
                continue

            # print("queue_item name:", job_name)
            queue_items.setdefault(job_name, []).append(qi_dct['id'])
        self.queue_items = queue_items

    def get_job(self, name):
        try:
            return self.jobs[name]
        except KeyError as ex:
            # print("self.jobs:", self.jobs.keys())
            raise UnknownJobException(self._public_job_url(name)) from ex

    def create_job(self, job_name, config_xml):
        self.post('/createItem', name=job_name,
                  headers={'Content-Type': 'application/xml header;charset=utf-8'},
                  payload=config_xml.encode('utf-8'))

    def delete_job(self, job_name):
        try:
            self.post('/job/' + job_name + '/doDelete')
        except ResourceNotFound as ex:
            # TODO: Check error
            raise UnknownJobException(self._public_job_url(job_name), ex) from ex

    def _set_description(self, description, build_url, replace=False, separator: str = '\n'):
        if not replace:
            dct = self.get_json(build_url, tree="description")
            existing_description = dct['description']
            if existing_description:
                description = existing_description + separator + description

        self.post(build_url + '/submitDescription', headers=_CT_URL_ENC, payload={'description': description})

    def set_build_description(
            self, description: str, replace: bool = False, separator: str = '\n',
            build_url: str = None, job_name: str = None, build_number: int = None):
        """Utility to set/append build description.

        Args:
            description:  The description to set on the build
            replace:      If True, replace existing description, if any, instead of appending to it
            separator:    A separator to insert between any existing description and the new :py:obj:`description` if :py:obj:`replace` is False.
            build_url:    The URL of the Jenkins job build.
            job_name:     Name of the Jenkins job
            build_number: The build number for which to set the description
        """

        self.poll()
        build_url = self.get_build_url(build_url, job_name, build_number)
        try:
            self._set_description(description, build_url, replace, separator)
        except ResourceNotFound as ex:
            raise ValueError(f"Build not found {repr(build_url)}", ex) from ex


class ApiJob():
    def __init__(self, jenkins, dct, name, has_children):
        self.jenkins = jenkins
        self.dct = dct.copy()
        self.name = name
        self.has_children = has_children
        self.public_uri = self.jenkins._public_job_url(self.name)  # pylint: disable=protected-access
        self.old_build_number = None
        self._invocations = OrderedDict()
        self.queued_why = None

        self._path = "/job/" + self.name

        for prop in self.dct.get("property", []):
            if prop and prop.get('parameterDefinitions'):
                self._build_trigger_path = self._path + "/buildWithParameters"
                return

        for action in self.dct.get("action", []):
            if action and action.get('parameterDefinitions'):
                self._build_trigger_path = self._path + "/buildWithParameters"
                return

        self._build_trigger_path = self._path + "/build"

    def invoke(self, securitytoken, build_params, cause, description):
        try:
            if cause:
                build_params = build_params or {}
                build_params['cause'] = cause
            headers = _CT_URL_ENC if build_params else None
            params = {}
            if securitytoken:
                params['token'] = securitytoken
            response = self.jenkins.post(self._build_trigger_path, headers=headers, payload=build_params, **params)
        except ResourceNotFound as ex:
            raise UnknownJobException(self.jenkins._public_job_url(self.name), ex) from ex  # pylint: disable=protected-access

        # Make location relative
        location = urllib.parse.urlsplit(response.headers['location']).path
        if self.jenkins.jenkins_prefix:
            location = os.path.relpath(location, self.jenkins.jenkins_prefix)

        old_inv = self._invocations.get(location)
        if old_inv:
            old_inv.build_number = _SUPERSEDED_PSEUDO_BUILD_NUM
        inv = self.jenkins.invocation_class(self, location, description)
        self._invocations[location] = inv
        # print("invoke:", location, inv)
        return inv

    def poll(self):
        for invocation in self._invocations.values():
            # print("invocation:", invocation)
            if not invocation.build_number:
                query = "executable[number],why,*"
                dct = self.jenkins.get_json(invocation.queued_item_path, tree=query)
                # print("dct:", dct)

                executable = dct.get('executable')
                if executable:
                    invocation.build_number = executable['number']
                    invocation.queued_why = None
                    invocation.set_description()
                else:
                    try:
                        invocation.queued_why = dct['why']
                        # If we still have invocations in the queue, wait until next poll to query again
                        break
                    except KeyError:
                        # 'scans' have no 'why'
                        pass

    def job_status(self):
        """Result, progress and latest buildnumber info for the JOB, NOT the invocation

        Return (result, progress_info, latest_build_number) (str, str, int or None):
            If there is no finished build, result will be BuildResult.UNKNOWN and latest_build_number will be None
        """
        progress = None

        if not self.has_children:
            qi = self.dct['queueItem']
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
                self.jenkins.post('/queue/cancelItem', id=repr(qid))
            except ResourceNotFound:
                # Job is no longer queued, so just ignore
                # NOTE: bug https://issues.jenkins-ci.org/browse/JENKINS-21311 also brings us here!
                pass

        # Abort running builds
        query = "builds[number,result]"
        dct = self.jenkins.get_json("/job/" + self.name, tree=query)
        for build in dct['builds']:
            _result, progress = _result_and_progress(build)
            if progress != Progress.IDLE:
                build_number = build['number']
                try:
                    self.jenkins.post(self._path + '/' + repr(build_number) + '/stop')
                except ResourceNotFound:  # pragma: no cover
                    # Build was deleted, just ignore
                    pass

    def update_config(self, config_xml):
        self.jenkins.post("/job/" + self.name + "/config.xml",
                          headers={'Content-Type': 'application/xml header;charset=utf-8'},
                          payload=config_xml.encode('utf-8'))

    def disable(self):
        try:
            self.jenkins.post(self._path + '/disable')
        except ResourceNotFound as ex:
            raise UnknownJobException(self.jenkins._public_job_url(self.name), ex) from ex  # pylint: disable=protected-access

    def enable(self):
        try:
            self.jenkins.post(self._path + '/enable')
        except ResourceNotFound as ex:
            raise UnknownJobException(self.jenkins._public_job_url(self.name), ex) from ex  # pylint: disable=protected-access

    def __repr__(self):
        return str(dict(name=self.name, dct=self.dct))


class Invocation(ApiInvocationMixin):
    def __init__(self, job, queued_item_path, description):
        self.job = job
        self.queued_item_path = queued_item_path
        self.description = description
        self.build_number = None
        self.queued_why = None

    def __repr__(self):
        return 'Invocation: ' + repr(self.queued_item_path) + ' ' + repr(self.build_number) + ' ' + repr(self.queued_why)

    def status(self):
        """Result and Progress info for the invocation

        Return (result, progress_info) (str, str):
            If the build has not started or has not finished running, result will be BuildResult.UNKNOWN
        """

        if self.build_number is None:
            return (BuildResult.UNKNOWN, Progress.QUEUED)

        if self.build_number == _SUPERSEDED_PSEUDO_BUILD_NUM:
            return (BuildResult.SUPERSEDED, Progress.IDLE)

        if self.build_number == _DEQUEUED_PSEUDO_BUILD_NUM:
            return (BuildResult.DEQUEUED, Progress.IDLE)

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
        dct = self.job.jenkins.get_json("/job/" + self.job.name, tree=query)
        for build in dct['builds']:
            if build['number'] == self.build_number:
                return _result_and_progress(build)

        raise Exception("Build deleted while flow running? This may happen if you invoke more builds than the job is configured to keep. " + repr(self))

    def set_description(self):
        """Sets the build description"""
        if not self.description:
            return

        build_url = self.job._path + '/' + repr(self.build_number)
        try:
            self.job.jenkins._set_description(self.description, build_url)
        except ResourceNotFound as ex:
            raise Exception("Build deleted while flow running? " + repr(build_url), ex) from ex

    def stop(self, dequeue):
        try:
            if self.build_number is not None and self.build_number >= 0 and not dequeue:
                # Job has started
                self.job.jenkins.post(self.job._path + '/' + repr(self.build_number) + '/stop')
                return

            if self.build_number is None and dequeue:
                # Job is queued
                qid = self.queued_item_path.strip('/').split('/')[2]
                self.job.jenkins.post('/queue/cancelItem', id=qid)
                self.build_number = _DEQUEUED_PSEUDO_BUILD_NUM
        except ResourceNotFound:  # pragma: no cover
            # Job is no longer queued or running, except that it may have just changed from queued to running
            # We leave it up to the flow logic to handle that
            # NOTE: bug https://issues.jenkins-ci.org/browse/JENKINS-21311 also brings us here!
            pass
