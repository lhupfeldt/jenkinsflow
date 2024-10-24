#!/bin/bash

exclude="test demo ordered_enum.py mocked.py setup.py"
sphinx-apidoc -f -A "Lars Hupfeldt Nielsen" -V 1.0 -R 1.0.0 --maxdepth 2 --full --separate -o docs/source/ ../jenkinsflow $exclude
