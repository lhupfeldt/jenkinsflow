import sys
import os.path


error_msg = """
`{pkg}` 4.0+ supports Python {min_sup_version} and above.
When using Python 2.7, 3.4 - 3.5.x please install {pkg} 3.x

Python {py} detected.

Make sure you have pip >= 9.0 as well as setuptools >= 24.2 to avoid these kinds of issues:

 $ pip install pip setuptools --upgrade

Your choices:

- Upgrade to Python {min_sup_version}+.

- Install an older version of {pkg}:

 $ pip install '{pkg}<9.0'

It would be great if you can figure out how this version ended up being
installed, and try to check how to prevent that for future users.

Source: https://github.com/lhupfeldt/{pkg}
"""

min_sup_version = (3, 6, 0)
if sys.version_info < min_sup_version:
    raise ImportError(error_msg.format(
        py='.'.join([str(vv) for vv in sys.version_info[:3]]),
        pkg=os.path.basename(os.path.dirname(os.path.abspath(__file__))),
        min_sup_version='.'.join([str(vv) for vv in min_sup_version])))
