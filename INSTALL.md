Installation
------------

1. Install jenkinsapi python library and other dependencies:
   pip install jenkinsapi enum34
   optional: pip install tenjin (if you want to use the template based job loader)

2. To use the experimental visualisation feature:  
   pip install bottle atomicfile

3. Make jenkinsflow files (flow.py and possibly unbuffered.py) available to your jenkins/hudson installation.

4. To use the warn_only (experimental) feature, jenkins url must be set in Jenkins configuration.

5. Read the file demo/demo_security.py for notes about security, if you have enabled security on your Jenkins

6. All set! You can now create jobs that have a shell execution step, which will a use this library to control the running of other jobs.
   See the demo directory for example flows. The demo jobs can be loaded by running tests, see below.


Test
----

1. Install pytest and tenjin template engine:
   pip install -U pytest pytest-cov pytest-cache pytest-instafail logilab-devtools tenjin proxytypes

2. Read and update the file demo/demo_security.py if you have enabled security on your Jenkins

3. Run the tests:
   # Mocked tests do not require Jenkins
   JENKINSFLOW_MOCK_API=true ./test.py

   # Load test jobs into Jenkins and execute them
   JENKINS_URL=<your jenkins> python ./test/tests.py

   Important:
   Jenkins is default configured with only two executors on master. To avoid timeouts in the test cases this must be raised to at least 8.
   Jenkins is default configured with a 'Quit period of 5 seconds'. To avoid timeouts in the test cases this should be set to 0.

   All jobs created by the test script are prefixed with 'jenkinsflow_', so they can easily be removed.


Demos
----

1. Run tests as described above to load jobs Jenkins

2. Demo scripts can be executed from command line:
   python ./demo/<demo>.py 

3. Demo scripts can be executed from the loaded jobs
   Jenkins needs to be able to find the scripts, the demo jobs are setup to find the scripts in '/tmp/jenkinsflow'.
   Run ./tmp_install.sh to install in /tmp/...
   Execute the demo flow jobs: 'jenkinsflow_demo__<demo-name>__0flow'

4. To see a live flow graph of the basic demo in your browser:
   Start 'python ./server.py' before running demo/basic.py
   Open localhost:9090 in your browser