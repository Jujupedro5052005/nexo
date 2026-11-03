"""Opt-in smoke. Requires BOTH explicit authorization variables and a key.

This module overrides the default network blocker only for explicitly enabled
smokes. No metadata test silently generates text, and generation is one call.
"""

import os

import pytest

from nexo.infrastructure.intelligence.config import AISettings
from nexo.infrastructure.intelligence.providers import GeminiIntelligenceProvider

LIVE = os.environ.get("NEXO_AI_LIVE_TEST") == "1"
pytestmark = pytest.mark.skipif(
    not LIVE, reason="Teste real requer NEXO_AI_LIVE_TEST=1 e credencial externa."
)


@pytest.fixture(autouse=True)
def forbid_external_network():
    if not LIVE:
        pytest.skip("Internet desabilitada por padrão.")


def test_live_model_metadata(storage):
    settings = AISettings.from_environment()
    if not settings.api_key:
        pytest.skip("Credencial ausente.")
    provider = GeminiIntelligenceProvider(settings, storage)
    try:
        assert "acessíveis" in provider.test_connection()
    finally:
        provider.close()


def test_live_single_authorized_generation(storage):
    if os.environ.get("NEXO_AI_ALLOW_LIVE_GENERATION") != "1":
        pytest.skip(
            "Geração real exige NEXO_AI_ALLOW_LIVE_GENERATION=1; pode consumir quota/custo."
        )
    settings = AISettings.from_environment()
    if not settings.api_key:
        pytest.skip("Credencial ausente.")
    settings = settings.model_copy(
        update={"max_output_tokens": 128, "daily_request_limit": 1}
    )
    provider = GeminiIntelligenceProvider(settings, storage)
    try:
        assert provider.synthesize("Responda somente: conexão Nexo operacional.")
        assert storage.usage()["requests"] == 1
    finally:
        provider.close()
