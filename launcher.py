"""Desktop executable entry point; startup offers both data environments."""

import sys
from multiprocessing import freeze_support
from pathlib import Path

# Running a clone only requires requirements.txt; frozen bundles resolve normally.
if not getattr(sys, "frozen", False):
    sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from nexo.main import cli

if __name__ == "__main__":
    freeze_support()
    raise SystemExit(cli())
