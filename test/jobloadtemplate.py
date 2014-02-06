# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import sys, os
from os.path import join as jp

here = os.path.abspath(os.path.dirname(__file__))
sys.path.append(jp(here, '../..'))

import tenjin
from tenjin.helpers import *
engine = tenjin.Engine()

from jenkinsflow.jobload import update_job


def update_job_from_template(jenkins, job_name, config_xml_template, pre_delete=False, params=(), exec_time=0.01):
    """
    config_xml_template: filename of tenjin xml template
    params: tuple of tuples (name, value, description)
    """

    config_xml = engine.render(config_xml_template, {'exec_time': exec_time, 'params': params or ()})
    update_job(jenkins, job_name, config_xml, pre_delete)
