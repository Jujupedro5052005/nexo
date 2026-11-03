"""Desktop executable entry point; startup offers both data environments."""

from multiprocessing import freeze_support

from nexo.main import cli

if __name__ == "__main__":
    freeze_support()
    raise SystemExit(cli())
