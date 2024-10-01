#!/usr/bin/env python3

# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import sys, os

import click

# Allow relative imports while running as script. Necessary for testing without installing
if __package__ is None:
    _here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(1, os.path.dirname(os.path.dirname(_here)))
    import jenkinsflow.cli
    __package__ = "jenkinsflow.cli"


from .set_build_description import set_build_description, set_build_description_hidden


@click.group()
def cli():
    """Commandline utilities for jenkinsflow"""


cli.add_command(set_build_description)
cli.add_command(set_build_description_hidden)  # Backwards compatibility


if __name__ == "__main__":
    cli(auto_envvar_prefix='JENKINSFLOW')
