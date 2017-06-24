# This file is for configuring security for the demo and test jobs
# See the basic.py demo for how to do this with your own flows

# Note:

# Securitytoken and username/password are two different ways of allowing api access to execute (build) a job.
# You will however need both authentication methods, since neither can be used for everything

# Securitytoken is SIGNIFICANTLY faster than username/password
# If securitytoken is set, it will be used for executing (building) the jobs
# Securitytoken MUST be used in order for the flow job to ammend the 'build cause' of jobs that it invokes, if username/password
# is used the cause will always be 'Invoked by <username>'

# Username and password are needed for creating jobs and for changing build status with the 'Propagation.FAILURE_TO_UNSTABLE' feature
# The ./test/test.py script will need to create Jenkins jobs which REQUIRES username/password

# In order for all tests to pass you must enable security, select a security realm and a select "Anyone can do anything" in "Authorization",
# "Logged-in users can do anything" + "Allow anonymous read access" or Matrix/Projext/Role based security.
# If you have enabled any security beyond "Anyone can do anything" you must set 'set_build_description_must_authenticate = True' below.

# If you are using Matrix/Projext/Role based security, then the test user defined below and the user 'jenkinsflow_authtest1' should have
# the following permissions:

#  Job:   Build Cancel Configure Create Delete Discover Read
#  Build: Update

# The 'Anonymous' user must have - Job: Discover
# The 'authenticated' group must have - Overall: Read, Job: Discover

# If using "Role-Based Strategy":
#  create an item-role 'jenkinsflow_test' with pattern 'jenkinsflow_.*' and assign the permissions, then add the test user to that group.
#  create a global role 'jenkinsflow_test' with Create permission, then add the test user to that group.
# Job creation does not work with a project role only, see: https://issues.jenkins-ci.org/browse/JENKINS-19934?attachmentViewMode=list

# Must be True unless "Anyone can do anything" or "Logged-in users can do anything" is selected in security settings.
default_use_login = True

set_build_description_must_authenticate = True

securitytoken = 'jenkinsflow_securitytoken'

username = 'jenkinsflow_jobrunner'
password = '123123'
