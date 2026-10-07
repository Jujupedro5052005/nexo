from pathlib import Path

import pytest

from nexo.infrastructure.market_data import config
from nexo.infrastructure.market_data.config import MarketSettings


def token_matches(settings, expected):
    # Return a bool so failed assertions never expand credential values.
    return settings.token == expected


def test_env_is_loaded_from_project_root_even_with_another_working_directory(
    tmp_path, monkeypatch, clean_brapi_environment
):
    root = tmp_path / "project"
    root.mkdir()
    (root / ".env").write_text(
        "BRAPI_TOKEN=TEST_TOKEN\nBRAPI_BATCH_SIZE=3\n", encoding="utf-8-sig"
    )
    monkeypatch.setattr(
        config, "__file__", str(root / "src/nexo/infrastructure/market_data/config.py")
    )
    monkeypatch.chdir(tmp_path)
    settings = MarketSettings.from_environment()
    assert token_matches(settings, "TEST_TOKEN")
    assert settings.batch_size == 3


@pytest.mark.parametrize(
    "primary,alias,expected",
    [
        ("primary", "alias", "primary"),
        ("", "alias", "alias"),
        ("   ", " alias ", "alias"),
        (" primary ", "", "primary"),
        ("", "", None),
    ],
)
def test_variable_precedence_and_whitespace(
    tmp_path, monkeypatch, clean_brapi_environment, primary, alias, expected
):
    monkeypatch.setenv("BRAPI_TOKEN", primary)
    monkeypatch.setenv("BRAPI_API_KEY", alias)
    settings = MarketSettings.from_environment(tmp_path / "absent.env")
    assert token_matches(settings, expected)


def test_existing_environment_wins_for_the_same_variable(
    tmp_path, monkeypatch, clean_brapi_environment
):
    path = tmp_path / ".env"
    path.write_text(
        "BRAPI_TOKEN=file-value\nBRAPI_API_KEY=file-alias\n", encoding="utf8"
    )
    monkeypatch.setenv("BRAPI_TOKEN", "environment-value")
    assert token_matches(MarketSettings.from_environment(path), "environment-value")


def test_name_precedence_is_applied_after_loading_each_variable(
    tmp_path, monkeypatch, clean_brapi_environment
):
    path = tmp_path / ".env"
    path.write_text("BRAPI_TOKEN=file-primary\n", encoding="utf8")
    monkeypatch.setenv("BRAPI_API_KEY", "environment-alias")
    assert token_matches(MarketSettings.from_environment(path), "file-primary")


def test_absent_env_and_legacy_variables_do_not_configure_brapi(
    tmp_path, monkeypatch, clean_brapi_environment
):
    monkeypatch.setenv("MARKET_API_KEY", "legacy-value")
    monkeypatch.setenv("MARKET_API_BASE_URL", "https://example.invalid")
    assert MarketSettings.from_environment(tmp_path / ".env").token is None


def test_template_is_safe_and_env_is_ignored():
    root = Path(__file__).resolve().parents[2]
    template = (root / ".env.example").read_text(encoding="utf8")
    assert "BRAPI_TOKEN=\n" in template and "https://brapi.dev/dashboard" in template
    assert "BRAPI_API_KEY" in template and "MARKET_API_KEY=" not in template
    assert ".env" in (root / ".gitignore").read_text(encoding="utf8").splitlines()
