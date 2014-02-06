# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from jenkinsapi.custom_exceptions import UnknownJob


def update_job(jenkins, job_name, config_xml, pre_delete=False):
    """config_xml: The config xml as a string"""
    try:
        if not pre_delete:
            job = jenkins.get_job(job_name)
            print 'Updating job:', job_name
            job.update_config(config_xml)
            return

        print 'Deleting job:', job_name
        jenkins.delete_job(job_name)
    except UnknownJob:
        pass

    print 'Creating job:', job_name
    jenkins.create_job(job_name, config_xml)
