|Build Status| |Documentation Status|

jenkinsflow
===========

Python API with high level build flow constructs (parallel/serial) for
Jenkins (and Hudson). Allows full scriptable control over the execution
of Jenkins jobs. Also allows running 'jobs' without using Jenkins (for
testing without reloading Jenkins jobs).

See INSTALL.md for installation and test setup. See demo/... for some
usage examples. I don't test continuously on Hudson, but patches are
welcome.

Thanks to Aleksey Maksimov for contributing various bits, including the
graph visualization.

.. |Build Status| image:: https://api.travis-ci.org/lhupfeldt/jenkinsflow.svg?branch=master
   :target: https://travis-ci.org/lhupfeldt/jenkinsflow
.. |Documentation Status| image:: https://readthedocs.org/projects/jenkinsflow/badge/?version=stable
   :target: https://jenkinsflow.readthedocs.org/en/stable/
