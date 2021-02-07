# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from os.path import join as jp

# Note: duplicated in tmp_install.sh and INSTALL.md
test_tmp_dir = "/tmp/jenkinsflow-test"
pseudo_install_dir = jp(test_tmp_dir, "jenkinsflow")
flow_graph_root_dir = jp(test_tmp_dir, "graphs")
job_script_dir = jp(test_tmp_dir, 'job')
