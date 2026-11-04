# Build with: python -m PyInstaller --noconfirm Nexo.spec
from pathlib import Path

root = Path(SPECPATH)
a = Analysis(
    [str(root / "launcher.py")],
    pathex=[str(root / "src")],
    binaries=[],
    datas=[(str(root / "src" / "nexo" / "resources"), "nexo/resources"), (str(root / "docs" / "ai" / "knowledge"), "knowledge")],
    hiddenimports=["sqlalchemy.dialects.sqlite.pysqlite"],
    hookspath=[],
    runtime_hooks=[],
    excludes=["pytest", "tkinter", "PySide6.QtQml", "PySide6.QtQuick"],
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="Nexo", debug=False,
          bootloader_ignore_signals=False, strip=False, upx=False, console=False,
          icon=str(root / "src/nexo/resources/icons/Nexo_Icone.ico"))
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="Nexo")
