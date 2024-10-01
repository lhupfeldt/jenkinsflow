"""Utilities used by both nox and pytest invocation"""

import argparse

from .cfg import ApiType, Urls


OPT_API = "--api"
OPT_JOB_LOAD = "--job-load"
OPT_JOB_DELETE = "--job-delete"
OPT_DIRECT_URL = "--direct-url"
OPT_MOCK_SPEEDUP = "--mock-speedup"


def add_options(parser):
    def _add_opt(opt, **kwargs):
        """Pytest uses it's own parser which works similar to ArgParse"""
        if isinstance(parser, argparse.ArgumentParser):
            parser.add_argument(opt, **kwargs)
            return

        # metavar="NAME",
        parser.addoption(opt, **kwargs)

    _add_opt(
        OPT_API,
        action="store",
        default=','.join(at.name for at in list(ApiType)),
        help=f"Comma separated list of APIs to test. Default is all defined apis: {','.join([at.name for at in list(ApiType)])}",
    )

    _add_opt(
        OPT_JOB_LOAD,
        action="store_true",
        default=True,
        help="Load Jenkins jobs - can be skipped to speed up testing if there are no changes to jobs and they are already loaded.",
    )

    _add_opt(
        OPT_JOB_DELETE,
        action="store_true",
        default=False,
        help="Delete Jenkins jobs before loading. May be necessary depending the changes to jobs (or for cleanup of obsolete jobs).",
    )

    _add_opt(
        OPT_DIRECT_URL,
        action="store",
        default=Urls.default_direct_url,
        help="Direct URL (i.e. non-proxied) of Jenkins server.",
    )

    _add_opt(
        OPT_MOCK_SPEEDUP,
        action="store",
        type=int,
        default=500,
        help="Time speedup for mock API tests. If set too high test may fail. If set low it just takes longer to run tests.",
    )
