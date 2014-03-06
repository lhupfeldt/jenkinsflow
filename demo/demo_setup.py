# This ensures that the demos can find jenkinsflow even though it has not been installed

import sys
import os.path
from os.path import join as jp
here = os.path.dirname(__file__)
sys.path.append(jp(here, '../..'))
