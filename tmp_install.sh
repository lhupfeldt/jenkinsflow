#!/bin/bash
set -u

target_dir=/tmp/jenkinsflow/

rsync -av --exclude .git --exclude '*~' --exclude '*.pyc' --exclude '__pycache__' ./ $target_dir
chmod -R a+r $target_dir
chmod a+x $(find $target_dir -type d)
chmod a+x $target_dir/{test,demo}/*.py
