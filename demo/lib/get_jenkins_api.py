import os

from jenkinsflow.jenkins_api import JenkinsApi

from . import demo_security as security


def get_jenkins_api():
    url = os.environ.get('JENKINS_URL') or "http://localhost:8080"
    jenkins_api = JenkinsApi(url, username=security.username, password=security.password) if security.default_use_login else JenkinsApi(url)
    return jenkins_api, security.securitytoken
