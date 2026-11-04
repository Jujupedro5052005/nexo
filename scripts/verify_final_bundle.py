"""Reject stale PYZ code and missing offline assets before shipping a build."""

import argparse
import hashlib
from pathlib import Path
from types import CodeType

from PyInstaller.archive.readers import CArchiveReader

ROOT = Path(__file__).resolve().parents[1]


def method(module: CodeType, class_name: str, method_name: str) -> CodeType:
    cls = next(c for c in module.co_consts if isinstance(c, CodeType) and c.co_name == class_name)
    return next(c for c in cls.co_consts if isinstance(c, CodeType) and c.co_name == method_name)


def verify(folder: Path) -> None:
    archive = CArchiveReader(str(folder / "Nexo.exe")).open_embedded_archive("PYZ.pyz")
    for module, cls, name in (
        ("nexo.ui.pages.presentation_page", "PresentationPage", "_finished"),
        ("nexo.ui.pages.presentation_page", "PresentationPage", "exit_fullscreen"),
        ("nexo.ui.pages.presentation_page", "PresentationWebPage", "acceptNavigationRequest"),
        ("nexo.ui.window_chrome", "ResizeFilter", "nativeEventFilter"),
    ):
        source = ROOT / "src" / Path(*module.split(".")).with_suffix(".py")
        expected = method(compile(source.read_text(encoding="utf-8-sig"), str(source), "exec"), cls, name)
        actual = method(archive.extract(module), cls, name)
        assert (actual.co_code, actual.co_names, actual.co_consts) == (expected.co_code, expected.co_names, expected.co_consts), f"PYZ desatualizado: {module}.{name}; refaça o build com --clean."
    for source in (ROOT / "src/nexo/resources").rglob("*"):
        if source.is_file():
            bundled = folder / "_internal/nexo/resources" / source.relative_to(ROOT / "src/nexo/resources")
            assert bundled.is_file(), f"Recurso ausente: {bundled}"
            assert hashlib.sha256(bundled.read_bytes()).digest() == hashlib.sha256(source.read_bytes()).digest()
    assert (folder / "_internal/PySide6/QtWebEngineProcess.exe").is_file()
    assert (folder / "_internal/PySide6/resources/qtwebengine_resources.pak").is_file()
    assert len(list((folder / "_internal/knowledge").rglob("*.md"))) >= 15
    print("PYZ atualizado, recursos offline e corpus de IA conferidos.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("folder", type=Path)
    verify(parser.parse_args().folder)
