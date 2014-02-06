import os, glob
from os.path import join as jp


def clean_jobs_state():
    state_dir = "/tmp/qf"
    for state_file in glob.glob(jp(state_dir, '*')):
        os.remove(state_file)
