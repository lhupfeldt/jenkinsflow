# Copyright (c) 2012 - 2024 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from pathlib import Path

from .jenkins_api import UnknownJobException

try:
    import tenjin
    from tenjin.helpers import *  # pylint: disable=wildcard-import
    _ENGINE = tenjin.Engine()
except ImportError:  # pragma: no cover
    _ENGINE = None


def update_job(jenkins, job_name, config_xml, pre_delete=False, background=False):
    """Update or create a job in Jenkins.

    Args:
        jenkins (jenkins_api.JenkinsApi): JenkinsApi instance used for accessing jenkins.
        job_name (str): The name of the job.
        config_xml (str): The Jenkins job config xml.
        pre_delete (boolean): I the job exists it will be deleted and re-created instead of being updated.
    """

    try:
        if not pre_delete:
            jenkins.poll()
            job = jenkins.get_job(job_name)
            print('Updating job:', job_name)
            job.update_config(config_xml)
            return

        print('Deleting job:', job_name)
        jenkins.delete_job(job_name)
    except UnknownJobException:
        pass

    print('Creating job:', job_name)
    jenkins.create_job(job_name, config_xml)
    if not background:
        jenkins.poll()


def update_job_from_template(jenkins, job_name, config_xml_template: Path|str, pre_delete=False, background=False, context: dict|None = None):
    """Create or update a job based on a `Tenjin` http://www.kuwata-lab.com/tenjin/ config.xml template.

    Args:
        config_xml_template: Filename of tenjin config.xml template.
        context: Values to be used for template substitution.

    See :py:func:`.update_job` for other parameters.
    """

    assert _ENGINE, "You must install tenjin (e.g.: pip install tenjin)"
    config_xml = _ENGINE.render(str(config_xml_template), context or {})
    update_job(jenkins, job_name, config_xml, pre_delete, background)
