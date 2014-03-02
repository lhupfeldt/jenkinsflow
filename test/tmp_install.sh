#!/bin/bash
set -u

source_dir=$(cd $(dirname $0)/.. && pwd)

# Note: duplicated in mock_api.py, demo/basic.py and INSTALL.md
target_dir=/tmp/jenkinsflow-test/jenkinsflow

mkdir -p $target_dir
rsync -a --exclude .git --exclude '*~' --exclude '*.pyc' --exclude '__pycache__' --exclude '*.cache' $source_dir/ $target_dir/
mkdir -p $target_dir/.cache
chmod -R a+r $target_dir
chmod a+wrx $(find $target_dir -type d)
chmod a+x $target_dir/{test,demo}/*.py
