# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

try:
    import tenjin
    from tenjin.helpers import *
    engine = tenjin.Engine()
except ImportError:  # pragma: no cover
    engine = None


def update_job(jenkins, job_name, config_xml, pre_delete=False, async=False):
    """config_xml: The config xml as a string"""

    is_flow_rest_api = hasattr(jenkins, 'quick_poll')
    if is_flow_rest_api:
        from .specialized_api import UnknownJobException
    else:
        from jenkinsapi.custom_exceptions import UnknownJob as UnknownJobException

    try:
        if not pre_delete:
            if is_flow_rest_api:  # TODO
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
    if not async:
        jenkins.poll()


def update_job_from_template(jenkins, job_name, config_xml_template, pre_delete=False, async=False, context=None):
    """
    Create or update a job based on a Tenjin template
    config_xml_template: filename of tenjin xml template
    params: tuple of tuples (name, value, description)
    """
    assert engine, "You must install tenjin (e.g.: pip install tenjin)"
    config_xml = engine.render(config_xml_template, context or {})
    update_job(jenkins, job_name, config_xml, pre_delete, async)
