from pathlib import Path
from runpy import run_path
from zipfile import ZipFile

import pytest

package = run_path(
    str(Path(__file__).resolve().parents[2] / "scripts" / "package_windows.py")
)["package"]


@pytest.fixture
def bundle(tmp_path):
    folder = tmp_path / "Nexo"
    internal = folder / "_internal"
    internal.mkdir(parents=True)
    (folder / "Nexo.exe").write_bytes(b"fixture, not a Windows executable")
    (internal / "library.dll").write_bytes(b"fixture")
    return folder


@pytest.mark.parametrize(
    "name",
    [".env", ".env.local", ".ENV.production", "nexo.db", "NEXO.DB-WAL",
     "nexo.sqlite-shm", "nexo.sqlite3-journal", "provider_usage.tmp"],
)
def test_package_rejects_local_data_before_modifying_bundle(bundle, tmp_path, name):
    (bundle / "_internal" / name).write_text("private fixture", encoding="utf-8")
    destination = tmp_path / "delivery.zip"
    destination.write_bytes(b"previous delivery")
    with pytest.raises(ValueError, match="dados/segredos"):
        package(bundle, destination)
    assert destination.read_bytes() == b"previous delivery"
    assert not (bundle / "LEIA-ME.txt").exists()


def test_package_creates_complete_zip_in_new_directory(bundle, tmp_path):
    destination = tmp_path / "delivery" / "Nexo.zip"
    assert package(bundle, destination) == destination
    with ZipFile(destination) as archive:
        assert set(archive.namelist()) == {
            "Nexo/Nexo.exe", "Nexo/_internal/library.dll",
            "Nexo/LEIA-ME.txt", "Nexo/.env.example",
        }
        assert "Não exige Python" in archive.read("Nexo/LEIA-ME.txt").decode()
    assert not destination.with_suffix(".zip.tmp").exists()


def test_package_requires_internal_folder(bundle, tmp_path):
    (bundle / "_internal" / "library.dll").unlink()
    (bundle / "_internal").rmdir()
    with pytest.raises(ValueError, match="_internal"):
        package(bundle, tmp_path / "delivery.zip")


def test_package_rejects_output_inside_bundle(bundle):
    with pytest.raises(ValueError, match="fora da pasta"):
        package(bundle, bundle / "delivery.zip")


def test_package_rejects_symlink_to_external_file(bundle, tmp_path):
    target = tmp_path / "external.txt"
    target.write_text("private fixture", encoding="utf-8")
    try:
        (bundle / "external.txt").symlink_to(target)
    except OSError:
        pytest.skip("Symlinks are unavailable on this machine.")
    with pytest.raises(ValueError, match="links simbólicos"):
        package(bundle, tmp_path / "delivery.zip")
