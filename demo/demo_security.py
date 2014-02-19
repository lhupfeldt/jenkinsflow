# This file is for configuring security for the demo and test jobs
# See the basic.py demo for how to do this with your own flows

# Note: securitytoken and username/password are two different ways of allowing api access to EXECUTE a job
# securitytoken is SIGNIFICANTLY faster than username/password

# The test script will need to create Jenkins jobs which requires username/password

# If securitytoken is set, it will be used for running the jobs, and username password is only used for creating jobs

securitytoken = 'jenkinsflow_securitytoken'

username = 'jenkinsflow_jobrunner'
password = '123123'
