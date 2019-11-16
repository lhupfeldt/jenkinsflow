#!/bin/bash
set -u

source_dir=$(cd $(dirname $0)/.. && pwd)
target_dir=$1

rsync -a --delete --delete-excluded --exclude .git --exclude '*~' --exclude '*.py[cod]' --exclude '__pycache__' --exclude '*.cache' $source_dir/ $target_dir/
mkdir -p $target_dir/.cache
chmod -R a+r $target_dir
chmod a+wrx $(find $target_dir -type d)
chmod a+x $target_dir/{test,demo}/*.py
