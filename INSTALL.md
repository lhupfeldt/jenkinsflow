Installation
------------

Python 3.6 or later is required.
A recent Jenkins is required.
Hudson may be supported, but it is not longer tested.

1. The easy way:
   Install python-devel (required by the psutil dependency of the script_api)
   E.g on fedora:
   sudo dnf install python-devel

   pip install --user -U .

   To uninstall:
   pip uninstall jenkinsflow

   Read the file demo/demo_security.py if you have security enabled your Jenkins.

Jenkinsflow uses it's own specialized 'jenkins_api' python module to access Jenkins, using the Jenkins rest api.

2. Manually:
2.1. Install dependencies:
   pip install requests click atomicfile

   optional: pip install tenjin (if you want to use the template based job loader)

2.2. Install dependencies for experimental features:
   To use the experimental script api:
     Install python-devel (see above)
     pip install psutil setproctitle

   To use the experimental visualisation feature:
     pip install bottle

2.3. Read the file demo/demo_security.py for notes about security, if you have enabled security on your Jenkins

2.4. All set! You can now create jobs that have a shell execution step, which will a use this library to control the running of other jobs.
   See the demo directory for example flows. The demo jobs can be loaded by running tests, see below.


Note: I think jenkinsflow should work on Windows, but it has not been tested.
   I'm SURE the test/run.py script will fail on Windows. There are a few Linux/Unix bits in the test setup. Check test/framework/config.py and
   test/tmp_install.sh. Patches are welcome:)


Test
----

0. The mocked and script_api test can be run using 'tox'
   pip install tox

1. The tests which actually run Jenkins jobs currently do not run under tox.

   Install pytest and tenjin template engine:
   pip install --user -U -r test/requirements.txt

   # The test will also test the generation of documentation, for this you need:
   pip install --user -U -r doc/requirements.txt


2. Important Jenkins setup and test preparation:
   Configure security -
      Some of the tests requires security to be enabled.
      You need to create two users in Jenkins:
      Read the file demo/demo_security.py and create the user specified.
      Create a user called 'jenkinsflow_authtest1', password 'abcæøåÆØÅ'. ( u'\u00e6\u00f8\u00e5\u00c6\u00d8\u00c5' )

   Set the number of executers -
      Jenkins is default configured with only two executors on master. To avoid timeouts in the test cases this must be raised to at least 32.
      This is necessary because some of the test cases will execute a large amount of jobs in parallel.

   Change the 'Quite period' -
      Jenkins is default configured with a 'Quiet period' of 5 seconds. To avoid timeouts in the test cases this must be set to 0.

   Set Jenkins URL -
     Jenkins: Manage Jenkins -> Configure System -> Jenkins Location -> Jenkins URL

     The url should not use 'localhost'

   Your Jenkins needs to be on the host where you are running the test. If it is not, you will need to make jenkinsflow available to Jenkins. See
   test/tmp_install.sh

3. Run the tests:
   Use tox
   or
   Use ./test/run.py to run the all tests.

   JENKINS_URL=<your Jenkins> python ./test/run.py --mock-speedup=100 --direct-url <non proxied url different from JENKINS_URL>

   Note: you may omit JENKINS_URL if your Jenkins is on http://localhost:8080.
   Note: you may omit --direct-url if your Jenkins is on http://localhost:8080

   The test script will run the test suite with mocked jenkins api, script_api and jenkins_api in parallel. The mocked api is a very fast test of the flow logic.
   Mocked tests and script_api tests do not require Jenkins.
   The test jobs are automatically created in Jenkins.

   It is possible to select a subset of the apis using the --apis option.

   The value given to --mock-speedup is the time speedup for the mocked tests. If you have a reasonably fast computer, try 2000.
   If you get FlowTimeoutException try a lower value.
   If you get "<job> is expected to be running, but state is IDLE" try a lower value.

   By default tests are run in parallel using xdist and jobs are not deleted (but will be updated) before each run.
   You should have 32 executors or more for this, the cpu/disk load will be small, as the test jobs don't really do anything except sleep.
   To disable the use of xdist use --job-delete.

   All jobs created by the test script are prefixed with 'jenkinsflow_', so they can easily be removed.

   The test suite creates jobs called ..._0flow. These jobs are not executed by the test suite, by you can run them to see what the flows look like in a Jenkins job.
   If your Jenkins is not secured, you must set username and password to '' in demo_security,  in order to be able to run all the ..._0flow jobs.

   To see more test options, run ./test/run.py ---help


Demos
----

1. Run tests as described above to load jobs into Jenkins

2. Demo scripts can be executed from command line:
   python ./demo/<demo>.py

3. Demo scripts can be executed from the loaded 'jenkinsflow_demo__<demo-name>__0flow' Jenkins jobs.
   Jenkins needs to be able to find the scripts, the run.py script creates a test installation.


Flow Graph Visualisation
-----------------------

1. To see a flow graph of the basic demo in your browser:
   Start 'python ./visual/server.py' --json-dir '/tmp/jenkinsflow-test/graphs/jenkinsflow_demo__basic' before running ./demo/basic.py
   Open localhost:9090 in your browser.

   The test suite also puts some other graps in subdirectories under '/tmp/jenkinsflow-test/graphs'.
   The 'visual' feature is still experimental and does not yet show live info about the running flow/jobs.

   If you run ...0flow jobs that generate graphs from Jenkins the json graph file will be put in the workspace.


Documentation
----

1. Install sphinx and extensions:
   pip install 'sphinx>=1.6' sphinxcontrib-programoutput

2. Build documentation:
   cd doc/source
   make html (or some other format supported by sphinx)
