# This file is for configuring security for the demo and test jobs
# See the basic.py demo for how to do this with your own flows

# Note: securitytoken and username/password are two different ways of allowing api access to execute (build) a job
# securitytoken is SIGNIFICANTLY faster than username/password, however it can not be used for everything

# The test script will need to create Jenkins jobs which requires username/password

# If securitytoken is set, it will be used for executing (building) the jobs
# username and password are needed for creating jobs and for changing build status with the 'warn_only' feature

securitytoken = 'jenkinsflow_securitytoken'

username = 'jenkinsflow_jobrunner'
password = '123123'
