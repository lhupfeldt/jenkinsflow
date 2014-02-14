# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

try:
    import tenjin
    from tenjin.helpers import *
    engine = tenjin.Engine()
except ImportError:
    engine = None

from jenkinsapi.custom_exceptions import UnknownJob


def update_job(jenkins, job_name, config_xml, pre_delete=False):
    """config_xml: The config xml as a string"""
    try:
        if not pre_delete:
            job = jenkins.get_job(job_name)
            print('Updating job:', job_name)
            job.update_config(config_xml)
            return

        print('Deleting job:', job_name)
        jenkins.delete_job(job_name)
    except UnknownJob:
        pass

    print('Creating job:', job_name)
    jenkins.create_job(job_name, config_xml)


def update_job_from_template(jenkins, job_name, config_xml_template, pre_delete=False, context=None):
    """
    Create or update a job based on a Tenjin template
    config_xml_template: filename of tenjin xml template
    params: tuple of tuples (name, value, description)
    """
    assert engine, "You must install tenjin (e.g.: pip install tenjin)"
    config_xml = engine.render(config_xml_template, context or {})
    update_job(jenkins, job_name, config_xml, pre_delete)
