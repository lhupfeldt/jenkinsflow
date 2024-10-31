#!/usr/bin/env python3

# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import click


from .set_build_description import set_build_description


@click.group()
def cli():
    """Commandline utilities for jenkinsflow"""


cli.add_command(set_build_description)


def main():
    cli(auto_envvar_prefix='JENKINSFLOW')


if __name__ == "__main__":
    main()
