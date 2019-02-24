import sys
import os.path
import warnings


if sys.version_info < (3,):
    warnings.warn('You are installing `{pkg}` with Python 2. {pkg} will soon become Python 3 only.'.format(
        pkg=os.path.basename(os.path.dirname(os.path.abspath(__file__)))), UserWarning)
