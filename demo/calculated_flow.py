#!/usr/bin/env python3

# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# Demonstrate that the flow can be dynamically calculated by the script

import sys, os, tempfile
import logging
from collections import OrderedDict

from jenkinsflow.flow import serial
from jenkinsflow.unbuffered import UnBuffered

import lib.get_jenkins_api


# Buffered output does not work well in Jenkins, so in case
# this is run from a Jenkins job, we want unbuffered output.
sys.stdout = UnBuffered(sys.stdout)


def main(api, securitytoken):
    logging.basicConfig()
    logging.getLogger("").setLevel(logging.WARNING)

    print("Doing stuff before flow ...")
    demo_name = 'jenkinsflow_demo__calculated_flow'

    graph_output_dir = os.path.join(tempfile.gettempdir(), demo_name + '_jenkins')
    if not os.path.exists(graph_output_dir):
        os.makedirs(graph_output_dir)

    g1_components = range(1)
    g2_components = range(2)
    g3_components = range(2)
    component_groups = OrderedDict((('g1', g1_components), ('g2', g2_components), ('g3', g3_components)))

    # Flow
    with serial(api, timeout=70, securitytoken=securitytoken, job_name_prefix=demo_name + '__', report_interval=3,
                # Write json flow graph to display in browser, see INSTALL.md
                json_dir=graph_output_dir, json_indent=4) as ctrl1:

        ctrl1.invoke('prepare')

        with ctrl1.parallel(timeout=0, report_interval=3) as ctrl2:
            for gname, group in component_groups.items():
                with ctrl2.serial(timeout=0, report_interval=3) as ctrl3:
                    for component in group:
                        ctrl3.invoke('deploy_component_' + gname + '_' + str(component))

        with ctrl1.parallel(timeout=0, report_interval=3) as ctrl2:
            ctrl2.invoke('report_deploy')
            ctrl2.invoke('prepare_tests')

        with ctrl1.parallel(timeout=40, report_interval=3) as ctrl2:
            with ctrl2.serial(timeout=40, report_interval=3) as ctrl3:
                ctrl3.invoke('test_ui')
                with ctrl3.parallel(timeout=0, report_interval=3) as ctrl4:
                    for gname, group in component_groups.items():
                        for component in group:
                            ctrl4.invoke('test_component_' + gname + '_' + str(component))
            ctrl2.invoke('test_x')

        ctrl1.invoke('report', password='Y', s1='tst_regression', c1='complete')
        ctrl1.invoke('promote')

    print("Doing stuff after flow ...")


if __name__ == '__main__':
    main(*lib.get_jenkins_api.get_jenkins_api())
