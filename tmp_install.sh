#!/bin/bash
set -u

target_dir=/tmp/jenkinsflow

rsync -av --exclude .git --exclude '*~' --exclude '*.pyc' --exclude '__pycache__' --exclude '*.cache' ./ $target_dir/
mkdir -p $target_dir/.cache
chmod -R a+r $target_dir
chmod a+wrx $(find $target_dir -type d)
chmod a+x $target_dir/{test,demo}/*.py
