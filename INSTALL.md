Installation
------------
In the following Jenkins also means Hudson unless otherwise stated.

1. The easy way:
   python setup.py install

   To uninstall:
   pip uninstall jenkinsflow

Jenkinsflow can use it's own 'specialized_api' or the generic 'jenkinsapi' (through the jenkinsapi_wrapper)
to access jenkins. For most use cases the specialized_api should perform better and put less load on Jenkins.
There may be some setups (e.g. thusands of jobs and few builds per job) where jenkinsapi will perform better.

2. Manually:
2.1. Install dependencies:
   To use 'specialized_api':
   pip install enum34 restkit
   optional: pip install tenjin (if you want to use the template based job loader)

   To use 'jenkinsapi':
   pip install enum34 jenkinsapi proxytypes
   # Jenkinsapi can be found here https://github.com/salimfadhley/jenkinsapi
   Note: If jenkinsapi is placed next to jenkinsflow, that version of jenkinsapi will be used for the tests.

   Note: if you use Hudson (3.x):
      a. You cannot use the pip installed jenkinsapi, instead get it from:
         https://github.com/henriklynggaard/jenkinsapi.git
         checkout the 'hudson_support' branch
      b. You need to install the REST API plugin and enable REST API

2.2. To use the experimental visualisation feature:
   pip install bottle atomicfile

2.3. Make jenkinsflow files (flow.py and possibly unbuffered.py) available to your Jenkins installation.

2.4. To use propagation=Propagation.FAILURE_TO_UNSTABLE feature, Jenkins URL must be set in Jenkins configuration.
   Note that this feature uses the 'cli' which has problems working over a proxy.

2.5. Read the file demo/demo_security.py for notes about security, if you have enabled security on your Jenkins

2.6. All set! You can now create jobs that have a shell execution step, which will a use this library to control the running of other jobs.
   See the demo directory for example flows. The demo jobs can be loaded by running tests, see below.


Note: I think jenkinsflow should work on Windows, but it has not been tested.
   I'm SURE the test/test.py script will fail on Windows. There are a few Linux/Unix bits in the test setup. Check test/framework/config.py and
   test/tmp_install.sh. Patches are welcome:)


Test
----

1. Install pytest and tenjin template engine:
   pip install -U pytest pytest-cov pytest-cache pytest-instafail logilab-devtools pytest-xdist tenjin proxytypes

2. Read and update the file demo/demo_security.py if you have enabled security on your Jenkins

3. Run the tests:
   You should use ./test/test.py to run the tests.
   I will first run the test suite with mocked jenkins api, not actually invoking any jenkins jobs, this tests the flow logic vey fast.
   If the mock test passes, the same testsuite is run with the real jenkins api invokin jenkins jobs. The test jobs are automatically created.

   # Mocked tests do not require Jenkins (but there will be a couple of xfails if jenkins is not running)
   JENKINSFLOW_MOCK_API=100 JENKINS_URL=<your Jenkins> python ./test/test.py
   # Or if you are using Hudson
   JENKINSFLOW_MOCK_API=100 HUDSON_URL=<your Hudson> python ./test/tests.py

   Note: you may omit JENKINS_URL if your jenkins is on localhot:8080, but you have to specify HUDSON_URL if you are running hudson!

   The value given to JENKINSFLOW_MOCK_API is the time time speedup for the mocked tests. If you have a reasonably fast computer, try 2000.
   If you get FlowTimeoutException try a lower value.
   If you get "<job> is expected to be running, but state is IDLE" try a lower value.

   To enable the use of xdist to run tests (not mocked) in parallel set JENKINSFLOW_SKIP_JOB_DELETE=true. You should have 32 executors or more for this.

   Important:
   Jenkins is default configured with only two executors on master. To avoid timeouts in the test cases this must be raised to at least 8.
   Jenkins is default configured with a 'Quiet period' of 5 seconds. To avoid timeouts in the test cases this should be set to 0.
   Your Jenkins needs to be on the host where you are running the test. If it is not, you will need to make jenkinsflow available to jenkins. See
   test/tmp_install.sh

   All jobs created by the test script are prefixed with 'jenkinsflow_', so they can easily be removed.

   The test suite creates jobs called ..._0flow. These jobs are not executed by the test suite, by you can run them to see what the flows look like in a Jenkins job.
   If your Jenkins is not secured, you must set username and password to '' in demo_security,  in order to be able to run all the ..._0flow jobs.

Demos
----

1. Run tests as described above to load jobs into Jenkins

2. Demo scripts can be executed from command line:
   python ./demo/<demo>.py

3. Demo scripts can be executed from the loaded 'jenkinsflow_demo__<demo-name>__0flow' Jenkins jobs.
   Jenkins needs to be able to find the scripts, the test.py script creates a test installation.

4. To see a flow graph of the basic demo in your browser:
   Start 'python ./visual/server.py' --json-dir '/tmp/jenkinsflow-test/graphs/jenkinsflow_demo__basic' before running ./demo/basic.py
   Open localhost:9090 in your browser

   The test suite also puts some other graps in subdirectories under '/tmp/jenkinsflow-test/graphs'
   The 'visual' feature is still experimental and does not yet show live info about the running flow/jobs

   If you run ...0flow jobs that generate graphs from Jenkins the json graph file will be put in the workspace


Documentation
----

1. Install sphinx and extensions
   pip install sphinx sphinxcontrib-napoleon sphinx-argparse

2. cd doc/source
   make html (or some other format supported by sphinx)
