#!/bin/bash
set -u

source_dir=$1
target_dir=$2

rsync -a --delete --delete-excluded --exclude .git --exclude '*~' --exclude '*.py[cod]' --exclude '__pycache__' --exclude '*.cache' $source_dir/ $target_dir/
chmod -R a+r $target_dir
chmod a+wrx $(find $target_dir -type d)
