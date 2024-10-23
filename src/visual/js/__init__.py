from pathlib import Path

raise ImportError(f"Directory '{Path(__file__).parent}' is a data dir, not a package.")
