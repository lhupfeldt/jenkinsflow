#!/usr/bin/python

import sys, os
from os.path import join as jp
here = os.path.abspath(os.path.dirname(__file__))

sys.path.append(jp(here, '../demo'))
import nested, single_level, single_level_errors, prefix, hide_password

os.chdir(here)

print "Validating demos"
for demo in nested, single_level, single_level_errors, prefix:
    print ""
    demo.main()


print ""
try:
    hide_password.main()
except Exception:
    pass
else:
    raise Exception("Expected exception")
