import os

from jenkinsflow.jenkins_api import Jenkins

from jenkinsflow.demo import demo_security as security


def get_jenkins_api():
    url = os.environ.get('JENKINS_URL') or os.environ.get('HUDSON_URL') or "http://localhost:8080"
    jenkins_api = Jenkins(url, username=security.username, password=security.password) if security.default_use_login else Jenkins(url)
    return jenkins_api, security.securitytoken
