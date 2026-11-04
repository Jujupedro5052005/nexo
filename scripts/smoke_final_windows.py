"""Native Windows UI smoke of an extracted delivery; no application test bridge."""

import argparse
import ctypes
import hashlib
import json
import os
import sqlite3
import subprocess
import tempfile
import time
from ctypes import wintypes
from pathlib import Path

from PySide6.QtWidgets import QApplication


def run(executable: Path, output: Path, development: bool = False) -> None:
    if os.name != "nt":
        raise RuntimeError("Requires a real Windows desktop")
    app = QApplication.instance() or QApplication([])
    output.mkdir(parents=True, exist_ok=True)
    user = ctypes.windll.user32
    user.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user.SetForegroundWindow.argtypes = [wintypes.HWND]
    user.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    user.ClientToScreen.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.POINT)]
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user.IsWindowVisible.argtypes = [wintypes.HWND]
    user.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user.MoveWindow.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.BOOL]
    user.SendMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user.SendMessageW.restype = ctypes.c_ssize_t
    user.IsZoomed.argtypes = [wintypes.HWND]
    user.IsIconic.argtypes = [wintypes.HWND]
    user.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]

    def wait(seconds=0.7):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            app.processEvents()
            time.sleep(0.03)

    with tempfile.TemporaryDirectory(prefix="nexo_final_smoke_", ignore_cleanup_errors=True) as directory:
        env = {**os.environ, "NEXO_DATA_DIR": directory, "NEXO_AI_PROVIDER": "mock",
               "NEXO_PROVIDER_TEST_MODE": "true",
               **{f"NEXO_{p}_SOFT_DAILY_BUDGET": "0" for p in ("YAHOO", "BRAPI", "BOLSAI", "CVM")}}
        command = [str(executable.resolve()), "--normal"]
        if development:
            command = [str(executable.resolve()), "-c", "import os; from pathlib import Path; Path(os.environ['NEXO_DATA_DIR'], 'ui.pid').write_text(str(os.getpid())); from nexo.main import cli; raise SystemExit(cli(['--normal']))"]

        def ui_pid():
            marker = Path(directory) / "ui.pid"
            return int(marker.read_text()) if development and marker.exists() else process.pid
        process = subprocess.Popen(command, cwd=directory, env=env)
        hwnd = None
        try:
            deadline = time.monotonic() + 60
            while process.poll() is None and time.monotonic() < deadline:
                found = []

                @callback_type
                def collect(handle, parameter, found=found):
                    pid = wintypes.DWORD()
                    user.GetWindowThreadProcessId(handle, ctypes.byref(pid))
                    title = ctypes.create_unicode_buffer(256)
                    user.GetWindowTextW(handle, title, 256)
                    if pid.value == ui_pid() and user.IsWindowVisible(handle) and title.value == "Nexo Invest":
                        found.append(handle)
                    return True

                user.EnumWindows(collect, 0)
                if found:
                    hwnd = found[0]
                    break
                wait(0.2)
            assert hwnd, f"Window did not open; exit={process.poll()}"
            user.MoveWindow(hwnd, 20, 20, 1440, 900, True)
            user.SetForegroundWindow(hwnd)
            wait(2)

            def capture(name):
                nonlocal hwnd
                wait()
                handles = []

                @callback_type
                def current(handle, parameter):
                    identity = wintypes.DWORD()
                    user.GetWindowThreadProcessId(handle, ctypes.byref(identity))
                    title = ctypes.create_unicode_buffer(256)
                    user.GetWindowTextW(handle, title, 256)
                    if identity.value == ui_pid() and user.IsWindowVisible(handle):
                        handles.append((handle, title.value))
                    return True

                user.EnumWindows(current, 0)
                print(name, "exit", process.poll(), "windows", handles, flush=True)
                hwnd = next((h for h, title in handles if title == "Nexo Invest"), hwnd)
                # Capture the desktop compositor, including the WebEngine GPU surface.
                rect = wintypes.RECT()
                user.GetWindowRect(hwnd, ctypes.byref(rect))
                pixmap = app.primaryScreen().grabWindow(0).copy(rect.left, rect.top, rect.right-rect.left, rect.bottom-rect.top)
                assert pixmap.save(str(output / (name + ".png")))

            def click(x, y):
                user.SetForegroundWindow(hwnd)
                wait(0.1)
                point = wintypes.POINT(x, y)
                user.ClientToScreen(hwnd, ctypes.byref(point))
                user.SetCursorPos(point.x, point.y)
                user.mouse_event(0x0002, 0, 0, 0, 0)
                user.mouse_event(0x0004, 0, 0, 0, 0)
                wait()

            def key(code):
                user.SetForegroundWindow(hwnd)
                wait(0.1)
                user.keybd_event(code, 0, 0, 0)
                user.keybd_event(code, 0, 2, 0)
                wait()

            capture("01-overview")
            click(100, 615)
            wait(4)
            capture("02-presentation")
            key(0x24)  # Home
            key(0x27)  # Right
            capture("03-slide-two")
            click(1000, 852)
            capture("03b-tour-overview")
            click(100, 615)
            capture("03c-return-tour-slide")
            click(905, 852)
            capture("03d-fullscreen")
            key(0x1B)
            capture("03e-restored")
            restored = wintypes.RECT()
            user.GetWindowRect(hwnd, ctypes.byref(restored))
            assert (restored.right-restored.left, restored.bottom-restored.top) == (1440, 900)
            click(100, 660)
            capture("04-settings")
            click(100, 570)
            capture("05-intelligence")
            click(100, 615)
            capture("06-return-slide")
            click(100, 480)
            capture("07-analysis")
            click(780, 330)
            capture("08-guide")
            click(780, 414)
            capture("09-education")
            rect = wintypes.RECT()
            user.GetWindowRect(hwnd, ctypes.byref(rect))
            edge = ((rect.top + 400) << 16) | (rect.right - 2)
            user.SetCursorPos(rect.right - 2, rect.top + 400)
            wait(0.1)
            assert user.SendMessageW(hwnd, 0x0084, 0, edge) == 11

            def double_title():
                point = wintypes.POINT(400, 18)
                user.ClientToScreen(hwnd, ctypes.byref(point))
                user.SetCursorPos(point.x, point.y)
                for _ in range(2):
                    user.mouse_event(0x0002, 0, 0, 0, 0)
                    user.mouse_event(0x0004, 0, 0, 0, 0)
                    wait(0.08)
                wait()

            double_title()
            assert user.IsZoomed(hwnd)
            capture("10-maximized")
            double_title()
            assert not user.IsZoomed(hwnd)
            capture("11-restored")
            before_drag = wintypes.RECT()
            user.GetWindowRect(hwnd, ctypes.byref(before_drag))
            point = wintypes.POINT(400, 18)
            user.ClientToScreen(hwnd, ctypes.byref(point))
            user.SetCursorPos(point.x, point.y)
            user.mouse_event(0x0002, 0, 0, 0, 0)
            wait(0.15)
            user.SetCursorPos(point.x + 40, point.y + 20)
            wait(0.2)
            user.mouse_event(0x0004, 0, 0, 0, 0)
            wait()
            after_drag = wintypes.RECT()
            user.GetWindowRect(hwnd, ctypes.byref(after_drag))
            assert after_drag.left != before_drag.left or after_drag.top != before_drag.top
            user.SetCursorPos(after_drag.right - 2, after_drag.top + 400)
            wait(0.5)
            user.mouse_event(0x0002, 0, 0, 0, 0)
            wait(0.5)
            for offset in range(0, 41, 5):
                user.SetCursorPos(after_drag.right - 2 + offset, after_drag.top + 400)
                wait(0.05)
            user.mouse_event(0x0004, 0, 0, 0, 0)
            wait()
            after_resize = wintypes.RECT()
            user.GetWindowRect(hwnd, ctypes.byref(after_resize))
            print("Resize", tuple(getattr(after_drag, f) for f in ("left", "top", "right", "bottom")), tuple(getattr(after_resize, f) for f in ("left", "top", "right", "bottom")), flush=True)
            assert after_resize.right-after_resize.left > after_drag.right-after_drag.left
            user.MoveWindow(hwnd, 20, 20, 1440, 900, True)
            click(1330, 18)
            assert user.IsIconic(hwnd)
            user.ShowWindow(hwnd, 9)
            capture("11b-move-resize-minimize-restored")
            user.PostMessageW(hwnd, 0x0010, 0, 0)
            assert process.wait(timeout=20) == 0
            database = Path(directory) / "nexo.db"
            with sqlite3.connect(database) as db:
                tables = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")]
                counts = {table: db.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
                          for table in tables if table in {"portfolios", "transactions", "portfolio_events"}}
            assert all(count == 0 for count in counts.values())
            process = subprocess.Popen(command, cwd=directory, env=env)
            deadline = time.monotonic() + 45
            while process.poll() is None and time.monotonic() < deadline:
                reopened = []

                @callback_type
                def find_reopened(handle, parameter, reopened=reopened):
                    identity = wintypes.DWORD()
                    user.GetWindowThreadProcessId(handle, ctypes.byref(identity))
                    if identity.value == ui_pid() and user.IsWindowVisible(handle):
                        reopened.append(handle)
                    return True

                user.EnumWindows(find_reopened, 0)
                if reopened:
                    hwnd = reopened[0]
                    break
                wait(0.2)
            assert reopened
            capture("12-reopened")
            user.SetForegroundWindow(hwnd)
            user.keybd_event(0x12, 0, 0, 0)  # Alt+Tab task switcher
            user.keybd_event(0x09, 0, 0, 0)
            user.keybd_event(0x09, 0, 2, 0)
            wait(0.5)
            app.primaryScreen().grabWindow(0).save(str(output / "13-alt-tab.png"))
            user.keybd_event(0x12, 0, 2, 0)
            key(0x1B)
            user.PostMessageW(hwnd, 0x0010, 0, 0)
            assert process.wait(timeout=20) == 0
            with sqlite3.connect(database) as db:
                assert all(db.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0] == count
                           for table, count in counts.items())
            result = {"status": "executável extraído abriu, navegou e fechou no Windows 10",
                      "executable_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
                      "financial_rows_after_ui_smoke": counts,
                      "captures": str(output), "paid_ai_calls": 0, "market_requests_authorized": 0}
            result["native_resize_hit_after_webengine"] = True
            result["double_click_maximize_restore"] = True
            result["close_reopen_financial_rows_unchanged"] = True
            result["system_move_resize_minimize_restore"] = True
            if development:
                result["status"] = "interface de desenvolvimento validada em desktop Windows; não é smoke do EXE"
            (output / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            print(json.dumps(result, ensure_ascii=False))
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=20)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("executable", type=Path)
    parser.add_argument("--output", type=Path, default=Path("tmp/final-extracted-smoke"))
    parser.add_argument("--development", action="store_true")
    args = parser.parse_args()
    run(args.executable, args.output, args.development)
