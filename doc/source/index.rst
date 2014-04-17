.. jenkinsflow documentation master file, created by
   sphinx-quickstart on Wed Apr 16 09:04:01 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to jenkinsflow's documentation!
=======================================

The jenkinsflow package is used for controlling the invocation of `Jenkins <http://jenkins-ci.org/>`_ jobs in complex parallel and serial "flows".
This effectively replaces the upstream/downstream dependencies in Jenkins with a fully scripted flow.
Despite the name, this package may also be used with `Hudson <http://hudson-ci.org/>`_.

Module contents
---------------

.. toctree::
   :maxdepth: 2

   jenkinsflow.flow
   jenkinsflow.specialized_api
   jenkinsflow.jenkinsapi_wrapper
   jenkinsflow.set_build_result
   jenkinsflow.jobload
   jenkinsflow.unbuffered

.. automodule:: jenkinsflow
    :members:
    :show-inheritance:


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

