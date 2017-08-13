# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function
from .jenkins_api import UnknownJobException

try:
    import tenjin
    from tenjin.helpers import *
    engine = tenjin.Engine()
except ImportError:  # pragma: no cover
    engine = None


def update_job(jenkins, job_name, config_xml, pre_delete=False, background=False):
    """Update or create a job in Jenkins.

    Args:
        jenkins (jenkins_api.Jenkins): Jenkins Api instance used for accessing jenkins.
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


def update_job_from_template(jenkins, job_name, config_xml_template, pre_delete=False, background=False, context=None):
    """Create or update a job based on a `Tenjin` http://www.kuwata-lab.com/tenjin/ config.xml template.

    Args:
        config_xml_template (str): Filename of tenjin config.xml template.
        context (dict): Values to be used for template substitution.

    See :py:func:`.update_job` for other parameters.
    """

    assert engine, "You must install tenjin (e.g.: pip install tenjin)"
    config_xml = engine.render(config_xml_template, context or {})
    update_job(jenkins, job_name, config_xml, pre_delete, background)
