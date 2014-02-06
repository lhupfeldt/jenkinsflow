Installation
------------

1. Install jenkinsapi python library:
   pip install jenkinsapi

2. Make jenkinsflow files (jobcontrol.py and possibly unbuffered.py) available on to your jenkins/hudson installation.

3. All set! You can now create jobs with a shell execution step, which will a use this library. See demo/... for example flows.


Test
----
1. Install tenjin template engine:
   pip install tenjin

2. Run the tests:
   # Mocked tests do not require Jenkins
   JENKINSFLOW_MOCK_API=true ./test.py

   # Load test jobs into Jenkins and execute them
   python ./test/tests.py
