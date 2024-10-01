"""
Utility library for noxfile.
"""

import os
from pathlib import Path
from typing import Sequence, Tuple, Dict

_HERE = Path(__file__).resolve().parent
_TOP_DIR = _HERE.parent.parent

from .cfg import ApiType, speedup


def cov_options_env(api_types: Sequence[str], coverage=True) -> Tuple[Sequence[str], Dict[str, str]]:
    """Setup coverage options.

    Return pytest coverage options, and env variables dict.
    """

    if not coverage:
        return ()

    if len(api_types) == 3:
        fail_under = 95
    elif ApiType.JENKINS in api_types:
        fail_under = 94
    elif ApiType.MOCK in api_types and ApiType.SCRIPT in api_types:
        fail_under = 90
    elif ApiType.MOCK in api_types:
        fail_under = 88
    else:
        fail_under = 85

    # Set coverage exclude lines based on selected API types
    api_exclude_lines = []
    if ApiType.JENKINS in api_types:
        if os.environ.get('HUDSON_URL'):
            # Parts of jenkins_api not used when hudson
            api_exclude_lines.append("if self.jenkins.is_jenkins")
            api_exclude_lines.append(r'if head_response.get\("X-Jenkins"\)')
        else:
            # Parts of jenkins_api not used when jenkins
            api_exclude_lines.append("else:  # Hudson")
            api_exclude_lines.append("self.is_jenkins = False")
            api_exclude_lines.append(r'if head_response.get\("X-Hudson"\)')

    if api_types == [ApiType.SCRIPT]:
        # Parts of api_base not used in script_api (overridden methods)
        api_exclude_lines.append(r"return (self.job.public_uri + '/' + repr(self.build_number) + '/console')")

    # Set coverage exclude files based on selected API type
    api_exclude_files = []
    if ApiType.JENKINS not in api_types:
        api_exclude_files.append("jenkins_api.py")
    if ApiType.SCRIPT not in api_types:
        api_exclude_files.append("script_api.py")

    return (
        [f'--cov={_TOP_DIR}', '--cov-report=term-missing', f'--cov-fail-under={fail_under}', f'--cov-config={_HERE/"coverage_rc"}'],
        {
            "COV_API_EXCLUDE_LINES": "\n".join(api_exclude_lines),
            "COV_API_EXCLUDE_FILES": "\n".join(api_exclude_files),
        }
    )


def parallel_options(parallel, api_types):
    args = []

    if api_types != [ApiType.MOCK]:
        # Note: 'forked' is required for the kill/abort_current test not to abort other tests
        args.append('--forked')

        # Note: parallel actually significantly slows down the test when only running mock
        if parallel:
            args.extend(['-n', '16'])

    return args
