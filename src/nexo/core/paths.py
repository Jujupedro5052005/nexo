"""Writable application data paths; existing development databases stay in place."""

import os
import sys
from pathlib import Path


def environment_file() -> Path:
    """External secrets stay beside the executable, never inside its bundle."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / ".env"
    return Path(__file__).resolve().parents[3] / ".env"


def bundled_knowledge_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent)) / "knowledge"
    return Path(__file__).resolve().parents[3] / "docs" / "ai" / "knowledge"


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
