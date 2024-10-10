"""Set __version__ property."""

from importlib.metadata import version  # type: ignore


__version__ = version("jenkinsflow")
