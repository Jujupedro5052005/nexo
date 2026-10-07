import pytest


@pytest.fixture
def clean_brapi_environment(monkeypatch):
    for name in ("BRAPI_TOKEN", "BRAPI_API_KEY", "BRAPI_BATCH_SIZE"):
        monkeypatch.setenv(name, "")
        monkeypatch.delenv(name)
