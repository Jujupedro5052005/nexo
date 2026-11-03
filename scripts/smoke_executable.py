"""Windows smoke: open the visual selector, capture it, close without creating data."""

import argparse
import ctypes
import json
import os
import sqlite3
import subprocess
import tempfile
import time
from contextlib import closing
from ctypes import wintypes
from pathlib import Path

from PySide6.QtWidgets import QApplication


def smoke(executable: Path, capture: Path, mode: str = "selector") -> None:
    if os.name != "nt":
        raise SystemExit("Este smoke usa janelas nativas do Windows.")
    executable = executable.resolve(strict=True)
    app = QApplication.instance() or QApplication([])
    user32 = ctypes.windll.user32
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user32.PostMessageW.argtypes = [
        wintypes.HWND,
        wintypes.UINT,
        wintypes.WPARAM,
        wintypes.LPARAM,
    ]
    with tempfile.TemporaryDirectory(prefix="nexo_executable_smoke_") as directory:
        environment = {
            **os.environ,
            "NEXO_DATA_DIR": directory,
            "NEXO_AI_PROVIDER": "mock",
            "NEXO_PROVIDER_TEST_MODE": "true",
            **{
                f"NEXO_{name}_SOFT_DAILY_BUDGET": "0"
                for name in ("YAHOO", "BRAPI", "BOLSAI", "CVM")
            },
        }
        process = subprocess.Popen(
            [str(executable), *([] if mode == "selector" else ["--" + mode])],
            cwd=directory,
            env=environment,
        )
        window = None
        try:
            deadline = time.monotonic() + 45
            while process.poll() is None and time.monotonic() < deadline:
                candidates = []

                @callback_type
                def collect(hwnd, _parameter, found=candidates):
                    identity = wintypes.DWORD()
                    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(identity))
                    if identity.value == process.pid and user32.IsWindowVisible(hwnd):
                        title = ctypes.create_unicode_buffer(256)
                        user32.GetWindowTextW(hwnd, title, 256)
                        found.append((hwnd, title.value))
                    return True

                user32.EnumWindows(collect, 0)
                window = next(
                    (
                        hwnd
                        for hwnd, title in candidates
                        if (
                            title == "Bem-vindo ao Nexo"
                            if mode == "selector"
                            else title == "Nexo Invest"
                            if mode == "normal"
                            else title.startswith("Nexo Invest") and title != "Nexo Invest"
                        )
                    ),
                    None,
                )
                if window:
                    app.processEvents()
                    time.sleep(0.5)
                    capture.parent.mkdir(parents=True, exist_ok=True)
                    screen = app.primaryScreen()
                    assert screen is not None and screen.grabWindow(int(window)).save(
                        str(capture)
                    )
                    user32.PostMessageW(window, 0x0010, 0, 0)  # WM_CLOSE
                    assert process.wait(timeout=15) == 0
                    if mode == "selector":
                        assert not list(Path(directory).glob("*.db"))
                    else:
                        stem = "nexo_demo" if mode == "demo" else "nexo"
                        assert (Path(directory) / (stem + ".db")).exists()
                        assert not (
                            Path(directory)
                            / ("nexo.db" if mode == "demo" else "nexo_demo.db")
                        ).exists()
                        with closing(
                            sqlite3.connect(
                                Path(directory) / (stem + "_intelligence.db")
                            )
                        ) as db:
                            records = [
                                json.loads(row[0])
                                for row in db.execute("SELECT body FROM documents")
                            ]
                            assert (
                                sum(bool(d.get("canonical_id")) for d in records) == 15
                            )
                        if mode == "demo":
                            with closing(
                                sqlite3.connect(Path(directory) / "nexo_demo.db")
                            ) as db:
                                assert db.execute(
                                    "SELECT COUNT(*) FROM portfolio_events"
                                ).fetchone()[0] == 21
                                assert (
                                    db.execute(
                                        "SELECT COUNT(*) FROM financial_goals"
                                    ).fetchone()[0]
                                    == 3
                                )
                    print(
                        f"Executavel: {mode} abriu e fechou; ambientes isolados, sem requisições remotas autorizadas."
                    )
                    return
                time.sleep(0.2)
            raise RuntimeError(f"O seletor não apareceu; saída={process.poll()}.")
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=15)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("executable", type=Path)
    parser.add_argument(
        "--capture", type=Path, default=Path("tmp/executable-startup.png")
    )
    parser.add_argument(
        "--mode", choices=("selector", "demo", "normal"), default="selector"
    )
    args = parser.parse_args()
    smoke(args.executable, args.capture, args.mode)
