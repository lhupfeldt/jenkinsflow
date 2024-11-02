|Build Status| |Coverage| |Documentation Status| |PyPi Package| |License|

jenkinsflow
-----------

Python API with high level build flow constructs (parallel/serial) for
Jenkins. Allows full scriptable control over the execution
of Jenkins jobs.
Allows a flow running on one Jenkins to control Jobs on other Jenkins instances.
Also allows running 'jobs' as python scripts locally without using Jenkins.

.. code:: python

    import os

    from jenkinsflow.flow import serial
    from jenkinsflow.jenkins_api import JenkinsApi


    def _flow():
        """Execute jobs on the same Jenkins that run the flow, or Jenkins on localhost if not running from a Jenkins job."""
        url = os.environ.get("JENKINS_URL") or "http://localhost:8080"
        username = os.environ["JENKINS_USERNAME"]
        token = os.environ["JENKINS_TOKEN"]

        # Jenkinsflow uses it's own specialized *JenkinsApi* to access Jenkins, using the Jenkins rest api.
        api = JenkinsApi(url, username=username, password=token)
        with serial(api, timeout=70, report_interval=3) as outer_ctrl:
            outer_ctrl.invoke("prepare")
            outer_ctrl.invoke("deploy_component")

            with outer_ctrl.parallel(timeout=0, report_interval=3) as report_prepare_ctrl:
                report_prepare_ctrl.invoke("report_deploy")
                report_prepare_ctrl.invoke("prepare_tests")

            with outer_ctrl.parallel(timeout=0, report_interval=3) as test_ctrl:
                test_ctrl.invoke("test_x")
                test_ctrl.invoke("test_y")

            outer_ctrl.invoke("report", password="Y", s1="tst", c1="complete")


    if __name__ == "__main__":
        _flow()

Output (assuming all jobs ran succesfully):

.. code-block:: console

    === Jenkinsflow ===

    Legend:
    Serial builds: []
    Parallel builds: ()
    Invocation-N (w/x,y/z):
        -N: 'Invocation N of same job', where N is invocation number which is increased every time a job has been explicitly
                invoked (as opposed to retried). '-N' is only present for jobs with multiple invocations.
        w=current retry invocation in current flow scope, x=max in scope, y=total number of invocations, z=total max invocations
    Elapsed time: 'after: x/y': x=time spent during current run of job, y=time elapsed since start of outermost flow

    --- Calculating flow graph ---
    serial flow: [
       job: 'prepare'
       job: 'deploy_component'
       parallel flow: (
          job: 'report_deploy'
          job: 'prepare_tests'
       )

       parallel flow: (
          job: 'test_x'
          job: 'test_y'
       )

       job: 'report'
    ]



    --- Getting initial job status ---
    serial flow: [
       job: 'prepare' Status IDLE - latest build: #275
       job: 'deploy_component' Status IDLE - latest build: #273
       parallel flow: (
          job: 'report_deploy' Status IDLE - latest build: #273
          job: 'prepare_tests' Status IDLE - latest build: #273
       )

       parallel flow: (
          job: 'test_x' Status IDLE - latest build: #273
          job: 'test_y' Status IDLE - latest build: #273
       )

       job: 'report' Status IDLE - latest build: #273
    ]

    Defined Invocation http://larsesmbp:8080/job/prepare
    Defined Invocation http://larsesmbp:8080/job/deploy_component
    Defined Invocation http://larsesmbp:8080/job/report_deploy
    Defined Invocation http://larsesmbp:8080/job/prepare_tests
    Defined Invocation http://larsesmbp:8080/job/test_x
    Defined Invocation http://larsesmbp:8080/job/test_y
    Defined Invocation http://larsesmbp:8080/job/report - parameters:
         c1 = 'complete'
         password = '******'
         s1 = 'tst'


    --- Starting flow ---

    Flow Invocation (1/1,1/1): ['prepare', 'deploy_component', ('report_deploy', 'prepare_tests'), ('test_x', 'test_y'), 'report']

    Job Invocation (1/1,1/1): http://larsesmbp:8080/job/prepare
    Build started: 'prepare' - http://larsesmbp:8080/job/prepare/276/console
    job: 'prepare' stopped running
    job: 'prepare' Status IDLE - build: #276
    SUCCESS: 'prepare' - build: http://larsesmbp:8080/job/prepare/276/console after: 0.929s/1.013s

    Job Invocation (1/1,1/1): http://larsesmbp:8080/job/deploy_component
    Build started: 'deploy_component' - http://larsesmbp:8080/job/deploy_component/274/console
    job: 'deploy_component' stopped running
    job: 'deploy_component' Status IDLE - build: #274
    SUCCESS: 'deploy_component' - build: http://larsesmbp:8080/job/deploy_component/274/console after: 0.755s/2.356s

    Flow Invocation (1/1,1/1): ('report_deploy', 'prepare_tests')

    Job Invocation (1/1,1/1): http://larsesmbp:8080/job/report_deploy
    job: 'report_deploy' Status QUEUED

    Job Invocation (1/1,1/1): http://larsesmbp:8080/job/prepare_tests
    job: 'prepare_tests' Status QUEUED
    Build started: 'report_deploy' - http://larsesmbp:8080/job/report_deploy/274/console
    job: 'report_deploy' stopped running
    job: 'report_deploy' Status IDLE - build: #274
    SUCCESS: 'report_deploy' - build: http://larsesmbp:8080/job/report_deploy/274/console after: 0.831s/3.774s
    Build started: 'prepare_tests' - http://larsesmbp:8080/job/prepare_tests/274/console
    job: 'prepare_tests' stopped running
    job: 'prepare_tests' Status IDLE - build: #274
    SUCCESS: 'prepare_tests' - build: http://larsesmbp:8080/job/prepare_tests/274/console after: 0.835s/3.855s
    Flow SUCCESS ('report_deploy', 'prepare_tests') after: 0.913s/3.855s

    Flow Invocation (1/1,1/1): ('test_x', 'test_y')

    Job Invocation (1/1,1/1): http://larsesmbp:8080/job/test_x
    job: 'test_x' Status QUEUED

    Job Invocation (1/1,1/1): http://larsesmbp:8080/job/test_y
    job: 'test_y' Status QUEUED
    Build started: 'test_x' - http://larsesmbp:8080/job/test_x/274/console
    job: 'test_x' stopped running
    job: 'test_x' Status IDLE - build: #274
    SUCCESS: 'test_x' - build: http://larsesmbp:8080/job/test_x/274/console after: 0.833s/5.277s
    Build started: 'test_y' - http://larsesmbp:8080/job/test_y/274/console
    job: 'test_y' stopped running
    job: 'test_y' Status IDLE - build: #274
    SUCCESS: 'test_y' - build: http://larsesmbp:8080/job/test_y/274/console after: 0.830s/5.358s
    Flow SUCCESS ('test_x', 'test_y') after: 0.914s/5.358s

    Job Invocation (1/1,1/1): http://larsesmbp:8080/job/report
    Build started: 'report' - http://larsesmbp:8080/job/report/274/console
    job: 'report' stopped running
    job: 'report' Status IDLE - build: #274
    SUCCESS: 'report' - build: http://larsesmbp:8080/job/report/274/console after: 0.756s/6.708s
    Flow SUCCESS ['prepare', 'deploy_component', ('report_deploy', 'prepare_tests'), ('test_x', 'test_y'), 'report'] after: 6.624s/6.708s

    --- Final status ---
    serial flow: [
       job: 'prepare' SUCCESS
       job: 'deploy_component' SUCCESS
       parallel flow: (
          job: 'report_deploy' SUCCESS
          job: 'prepare_tests' SUCCESS
       )

       parallel flow: (
          job: 'test_x' SUCCESS
          job: 'test_y' SUCCESS
       )

       job: 'report' SUCCESS
    ]

    Finished: SUCCESS

See ``demo/...`` for some usage examples.
The demo jobs can be loaded by running tests, see below.

Installation
------------

Python 3.9 or later is required.
A recent Jenkins is required.

#. Install *python-devel* (required by the *psutil* dependency of the *script_api*)
   E.g on fedora::

        sudo dnf install python-devel

#. Install ``jenkinsflow``::

        pip install --user --upgrade jenkinsflow


#. Read the file ``demo/demo_security.py`` if you have security enabled your Jenkins.

All set! You can now create jobs which will a use this library to control the running of other jobs.

.. note::

   I think jenkinsflow should work on Windows, but it has not been tested.
   I'm SURE the tests will fail on Windows. There are a few Linux/Unix bits in the test setup. Check ``test/framework/cfg`` and
   ``noxfile.py``. Patches are welcome:)


Test
----

#. The test can be run using ``nox``::

    pip install nox

   There are three different apis for running the unit tests, **jenkins**, **script** and **mock**.
   The **mock** and **script** api test do not require any Jenkins setup. The **mock** api ony tests the flow logic, it does not exeute any jobs.
   See the '--api' option below.

#. Important Jenkins setup and test preparation

   - Configure security

     Some of the tests requires security to be enabled.
     You need to create two users in Jenkins:
     Read the file *demo/demo_security.py* and create the user specified.
     Create a user called **jenkinsflow_authtest1**, password **abcæøåÆØÅ**. ( u'\u00e6\u00f8\u00e5\u00c6\u00d8\u00c5' )

   - Set the number of executers

     Jenkins is default configured with only two executors on 'built-in' node. To avoid time-outs in the test cases this must be raised to at least **32**.
     This is necessary because some of the test cases will execute a large amount of jobs in parallel.

   - Change the 'Quite period'

     Jenkins is default configured with a 'Quiet period' of 5 seconds. To avoid time-outs in the test cases this must be set to **0**.

   - Set Jenkins URL

     Jenkins: Manage Jenkins -> Configure System -> Jenkins Location -> Jenkins URL

     The URL should **not** use **localhost**.

   Your Jenkins needs to be on the host where you are running the test. If it is not, you will need to make jenkinsflow available to Jenkins. See
   *test/framework/tmp_install.sh*

   .. note::

      To run the GitHub folder job test a GitHub test repository is needed! TODO: Describe the setup.

#. Run the tests using ``nox``::

       JENKINS_URL=<your Jenkins> nox --mock-speedup=100 --direct-url <non proxied URL different from JENKINS_URL>

   .. note::

     You may omit JENKINS_URL if your Jenkins is on http://localhost:8080.

   .. note::

     You may omit --direct-url if your Jenkins is on http://localhost:8080.

   .. note::

     Run ``nox -s unit -- --help`` and look at *custom options:* to see special options for unit tests.

   The test script will run the test suite with *mocked jenkins_api*, *script_api* and *jenkins_api* in parallel. The mocked api is a very fast test of the flow logic.
   Mocked tests and script-api tests do not require Jenkins.
   The test jobs are automatically created in Jenkins.

   It is possible to select a subset of the apis using the ``--api`` option.

   The value given to ``--mock-speedup`` is the time speedup for the mocked tests. If you have a reasonably fast computer, try **2000**.
   If you get ``FlowTimeoutException`` try a lower value.
   If you get *\<job\> is expected to be running, but state is IDLE* try a lower value.

   By default tests are run in parallel using xdist and jobs are not deleted (but will be updated) before each run.
   You should have **32** executors or more for this, the CPU/disk load will be small, as the test jobs don't really do anything except sleep.
   To disable the use of xdist use ``--job-delete``.

   All jobs created by the test script are prefixed with **jenkinsflow_**, so they can be easily removed.

   The test suite creates jobs called *..._0flow*. These jobs are not executed by the test suite, by you can run them to see what the flows look like in a Jenkins job.
   If your Jenkins is not secured, you must set username and password to '' in *demo_security.py*,  in order to be able to run all the ..._0flow jobs.


Demos
-----

#. Run tests as described above to load jobs into Jenkins

#. Demo scripts can be executed from command line::

        python ./demo/<demo>.py

#. Demo scripts can be executed from the loaded 'jenkinsflow_demo__<demo-name>__0flow' Jenkins jobs.
   Jenkins needs to be able to find the scripts, executing ``nox`` creates a test installation.


Flow Graph Visualisation
------------------------

To see a flow graph of the basic demo in your browser, execute::

     python ./visual/server.py' --json-dir '/tmp/jenkinsflow-test/graphs/jenkinsflow_demo__basic

before running ``./demo/basic.py``

Open http://localhost:9090 in your browser.

The test suite also puts some other graphs in subdirectories under */tmp/jenkinsflow-test/graphs*.
The *visual* feature is still experimental and does not yet show live info about the running flow/jobs.

If you run *...0flow* jobs that generate graphs from Jenkins the json graph file will be put in the workspace.


Documentation
-------------

Run ``nox`` to build documentation::

    nox -s docs


.. |Build Status| image:: https://app.travis-ci.com/lhupfeldt/jenkinsflow.svg?branch=master
   :target: https://app.travis-ci.com/lhupfeldt/jenkinsflow
.. |Documentation Status| image:: https://readthedocs.org/projects/jenkinsflow/badge/?version=stable
   :target: https://jenkinsflow.readthedocs.org/en/stable/
.. |PyPi Package| image:: https://badge.fury.io/py/jenkinsflow.svg
   :target: https://badge.fury.io/py/jenkinsflow
.. |Coverage| image:: https://coveralls.io/repos/github/lhupfeldt/jenkinsflow/badge.svg?branch=master
   :target: https://coveralls.io/github/lhupfeldt/jenkinsflow?branch=master
.. |License| image:: https://img.shields.io/github/license/lhupfeldt/jenkinsflow.svg
   :target: https://github.com/lhupfeldt/jenkinsflow/blob/master/LICENSE.TXT
