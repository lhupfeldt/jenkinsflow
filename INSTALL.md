Installation
------------

1. Install jenkinsapi python library:
   pip install jenkinsapi
   optional: pip install tenjin (if you want to use the template based job loader)

2. Make jenkinsflow files (jobcontrol.py and possibly unbuffered.py) available on to your jenkins/hudson installation.

3. To use the warn_only (experimental) feature, jenkins url must be set in Jenkins configuration.

4. All set! You can now create jobs that have a shell execution step, which will a use this library to control the running of other jobs.
   See demo/... for example flows.


Test
----
1. Install tenjin template engine:
   pip install -U pytest pytest-cov logilab-devtools tenjin proxytypes

2. Run the tests:
   # Mocked tests do not require Jenkins
   JENKINSFLOW_MOCK_API=true ./test.py

   # Load test jobs into Jenkins and execute them
   JENKINS_URL=<your jenkins> python ./test/tests.py

   Important:
   Jenkins is default configured with only two executors on master. To avoid timeouts in the test cases this must be raised to at least 8.
   Jenkins is default configured with a 'Quit period of 5 seconds'. To avoid timeouts in the test cases this should be set to 0.
