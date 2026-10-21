"""Writable application data paths; existing development databases stay in place."""

import os
import sys
from pathlib import Path


def application_data_dir() -> Path:
    configured = os.environ.get("NEXO_DATA_DIR", "").strip()
    if configured:
        path = Path(configured).expanduser()
        if not path.is_absolute():
            raise ValueError("NEXO_DATA_DIR deve ser um caminho absoluto.")
        return path.resolve()
    if getattr(sys, "frozen", False):
        return (
            Path(os.environ.get("LOCALAPPDATA") or Path.home() / ".local" / "share")
            / "NexoInvest"
        )
    return Path(__file__).resolve().parents[3] / "data"
