Installation
------------

In the following Jenkins also means Hudson, unless otherwise stated, python means python 2.7 or python3.4
or later and pip means python 2 pip or python 3 pip, unless differences are mentioned.

1. The easy way:
   python setup.py install

   To uninstall:
   pip uninstall jenkinsflow

   Read the file demo/demo_security.py if you have security enabled your Jenkins.

Jenkinsflow uses it's own specialized 'jenkins_api' python module to access Jenkins, using the Jenkins rest api.

2. Manually:
2.1. Install dependencies:
   pip2 install requests enum34 subprocess32 click atomicfile

   or

   pip3 install requests click atomicfile

   optional: pip install tenjin (if you want to use the template based job loader)

   Note: if you use Hudson (3.x): You need to configure Hudson to install the REST API plugin and enable REST API.

2.2. Install dependencies for experimental features:
   To use the experimental script api:
     pip install psutil setproctitle

   To use the experimental visualisation feature:
     pip install bottle

2.3. To use propagation=Propagation.FAILURE_TO_UNSTABLE feature, Jenkins URL must be set in Jenkins configuration.
   Note that this feature uses the 'cli' which has problems working over a proxy.
   This requires java to run the cli
   # NOTE: Some versions of Jenkins, e.g. 1.651.2, come with a broken cli, missing the main manifest attribute!

2.4. Read the file demo/demo_security.py for notes about security, if you have enabled security on your Jenkins

2.5. All set! You can now create jobs that have a shell execution step, which will a use this library to control the running of other jobs.
   See the demo directory for example flows. The demo jobs can be loaded by running tests, see below.


Note: I think jenkinsflow should work on Windows, but it has not been tested.
   I'm SURE the test/run.py script will fail on Windows. There are a few Linux/Unix bits in the test setup. Check test/framework/config.py and
   test/tmp_install.sh. Patches are welcome:)


Test
----

# NOTE: Some versions of Jenkins, e.g. 1.651.2, come with a broken cli, missing the main manifest attribute, making some tests fail!

0. The mocked and script_api test can be run using 'tox'
   pip install tox

1. The tests which actually run Jenkins jobs currently do not run under tox.

   Install python-devel
   E.g on fedora:
   sudo dnf install python-devel
   or
   sudo dnf install python3-devel

   Install pytest and tenjin template engine:
   pip install -U 'pytest>=2.7.2' 'pytest-cov>=2.1.0' 'pytest-cache>=1.0' 'pytest-instafail>=0.3.0' 'pytest-xdist>=1.12' tenjin click bottle

   pip2 install -U proxytypes
   or
   pip3 install -U objproxies

   # The test will also test the generation of documentation, for this you need:
   pip install -U 'sphinx>=1.6' sphinxcontrib-programoutput


2. Important Jenkins/Hudson setup and test preparation:
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

   Set Jenkins URL or Hudson url -
     Jenkins: Manage Jenkins -> Configure System -> Jenkins Location -> Jenkins URL
     Hudson: Manage Hudson -> Configure System -> E-mail Notification -> Hudson url

     The url should not use 'localhost'

   Your Jenkins needs to be on the host where you are running the test. If it is not, you will need to make jenkinsflow available to Jenkins. See
   test/tmp_install.sh

3. Run the tests:
   Use tox
   or
   Use ./test/run.py to run the all tests.

   JENKINS_URL=<your Jenkins> python ./test/run.py --mock-speedup=100 --direct-url <non proxied url different from JENKINS_URL>
   # Or if you are using Hudson:
   HUDSON_URL=<your Hudson> python ./test/run.py --mock-speedup=100  --direct-url <non proxied url different from HUDSON_URL>

   Note: you may omit JENKINS_URL/HUDSON_URL if your Jenkins/Hudson is on http://localhost:8080.
   Note: you may omit --direct-url if your Jenkins or Hudson is on http://localhost:8080
   Note: Because of timing dependencies when creating new jobs in Hudson, the first test run or any test run with --job-delete against Hudson will likely fail.

   The test script will run the test suite with mocked jenkins api, script_api and jenkins_api in parallel. The mocked api is a very fast test of the flow logic.
   Mocked tests and script_api tests do not require Jenkins.
   The test jobs are automatically created in Jenkins.

   It is possible to select a subset of the apis using the --apis option.

   The value given to --mock-speedup is the time time speedup for the mocked tests. If you have a reasonably fast computer, try 2000.
   If you get FlowTimeoutException try a lower value.
   If you get "<job> is expected to be running, but state is IDLE" try a lower value.

   By default tests are run in parallel using xdist and jobs are not deleted (but will be updated) before each run.
   You should have 32 executors or more for this, the cpu/disk load will be small, as the test jobs don't really do anything except sleep.
   Note: Parallel run is disabled when testing against Hudson, Hudson (3.2 at the time of writing) can't cope with the load, it throws NullPointerExceptions.
   To disable the use of xdist to run tests in parallel use --job-delete

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
