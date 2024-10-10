.. jenkinsflow documentation master file, created by
   sphinx-quickstart on Wed Apr 16 09:04:01 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to jenkinsflow's documentation!
=======================================

The jenkinsflow package is used for controlling the invocation of `Jenkins <http://jenkins-ci.org/>`_ jobs in complex parallel and serial "flows".
This effectively replaces the upstream/downstream dependencies in Jenkins with a fully scripted flow.
Note: this version requires Python 3.9.0 or newer. Use an older version for Python 3.6+ support.

Package contents
----------------

.. toctree::
   :maxdepth: 2

   jenkinsflow.flow
   jenkinsflow.jenkins_api
   jenkinsflow.script_api
   jenkinsflow.jobload
   jenkinsflow.unbuffered
   jenkinsflow.utils.set_build_description


Utility Scripts
---------------

.. toctree::
   :maxdepth: 2

   jenkinsflow

.. automodule:: jenkinsflow
    :members:
    :show-inheritance:


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

