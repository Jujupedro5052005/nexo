import json
from unittest.mock import Mock

import pytest

from nexo.domain.models.intelligence import AnalysisRequest, IntelligenceError
from nexo.infrastructure.intelligence.composition import create_workspace
from nexo.infrastructure.intelligence.config import AISettings
from nexo.infrastructure.intelligence.providers import GeminiIntelligenceProvider

from .test_gemini import sdk_response
from .test_mission2 import investigation_data  # noqa: F401
from .test_mission2_portfolio import (
    portfolio_investigation as portfolio_investigation,  # noqa: PLC0414
)


@pytest.mark.parametrize(
    "question,mode",
    [
        ("Devo comprar ou vender PETR4?", "chat"),
        (
            "Analise este ativo, com valuation, qualidade, riscos e cenários. PETR4 e como impacta na minha carteira atualmente, devo vender ou comprar no preço atual?",
            "deep",
        ),
    ],
)
def test_reported_scope_regressions(portfolio_investigation, question, mode):
    response = portfolio_investigation.ask(
        AnalysisRequest(question=question, portfolio_id=1, analysis_mode=mode)
    )
    assert [a["symbol"] for a in response.report["assets"]] == ["PETR4"]
    assert response.report["assets"][0]["position"] is not None


@pytest.mark.parametrize(
    "question,symbols",
    [
        ("Analise PETR4 e seu impacto na minha carteira.", {"PETR4"}),
        ("Compare PETR4 e VALE3.", {"PETR4", "VALE3"}),
        ("Analise toda minha carteira.", {"ITUB4", "PETR4", "EGIE3"}),
    ],
)
def test_explicit_scope(portfolio_investigation, question, symbols):
    response = portfolio_investigation.ask(
        AnalysisRequest(question=question, portfolio_id=1)
    )
    assert {a["symbol"] for a in response.report["assets"]} == symbols


def test_followup_and_new_ticker(portfolio_investigation):
    ask = portfolio_investigation.ask
    ask(AnalysisRequest(question="Devo comprar PETR4?", portfolio_id=1))
    revised = ask(
        AnalysisRequest(
            question="E se a margem de segurança fosse de 25%?", portfolio_id=1
        )
    )
    assert [a["symbol"] for a in revised.report["assets"]] == ["PETR4"]
    assert revised.report["assets"][0]["scenarios"][1]["safety_discount"] == "0.25"
    changed = ask(AnalysisRequest(question="Analise VALE3", portfolio_id=1))
    assert [a["symbol"] for a in changed.report["assets"]] == ["VALE3"]


def test_concept_does_not_query_market(portfolio_investigation):
    tools = portfolio_investigation.orchestrator.tools
    tools.execute = Mock(side_effect=AssertionError("Concept queried market"))
    portfolio_investigation.ask(
        AnalysisRequest(
            question="Explique o modelo de Gordon.",
            portfolio_id=1,
            analysis_mode="deep",
        )
    )
    tools.execute.assert_not_called()


def gemini_workspace(workspace, *, fail=False, data_mode="normal"):
    client = Mock()
    answer = "PETR4: manter e acompanhar antes de ampliar. A cotação observada deve ser confrontada com os cenários estimados e com o peso da posição na carteira. Os proventos históricos não garantem renda futura; reveja a tese se lucro, endividamento ou premissas mudarem."
    client.models.generate_content.return_value = sdk_response(answer)
    if fail:
        client.models.generate_content.side_effect = RuntimeError(
            "external details must stay private"
        )
    composed = create_workspace(
        AISettings(api_key="test-placeholder", provider="auto"),
        workspace.storage,
        workspace.orchestrator.tools,
        include_library=False,
        data_mode=data_mode,
    )
    assert isinstance(composed.orchestrator.provider, GeminiIntelligenceProvider)
    composed.orchestrator.provider.client = client
    return composed, client, answer


@pytest.mark.parametrize("data_mode", ["normal", "demo"])
def test_real_adapter_synthesis_receives_target_and_position(
    portfolio_investigation, data_mode
):
    workspace, client, answer = gemini_workspace(
        portfolio_investigation, data_mode=data_mode
    )
    response = workspace.ask(
        AnalysisRequest(
            question="Devo comprar ou vender PETR4?",
            portfolio_id=1,
            allow_cloud=True,
            allow_estimates=False,
        )
    )
    assert response.mode == "gemini" and answer in response.markdown
    assert workspace.status()["mode"] == "Gemini"
    context = json.loads(client.models.generate_content.call_args.kwargs["contents"])
    assert [a["symbol"] for a in context["analysis"]["assets"]] == ["PETR4"]
    assert context["analysis"]["assets"][0]["position"]
    assert client.models.generate_content.call_count == 1


def test_gemini_failure_never_turns_into_local_answer(portfolio_investigation):
    workspace, _, _ = gemini_workspace(portfolio_investigation, fail=True)
    with pytest.raises(IntelligenceError, match="Gemini"):
        workspace.ask(
            AnalysisRequest(
                question="Devo comprar PETR4?",
                portfolio_id=1,
                allow_cloud=True,
                allow_estimates=False,
            )
        )
    assert portfolio_investigation.history("default") == ()


def test_gemini_requires_consent(portfolio_investigation):
    workspace, client, _ = gemini_workspace(portfolio_investigation)
    with pytest.raises(IntelligenceError, match="Autorize"):
        workspace.ask(AnalysisRequest(question="Devo comprar PETR4?", portfolio_id=1))
    client.models.generate_content.assert_not_called()


@pytest.mark.parametrize("external", [True, False])
def test_frozen_env_selection_and_precedence(tmp_path, monkeypatch, external):
    from nexo.core import paths

    folder = tmp_path / "bundle"
    folder.mkdir()
    (tmp_path / ".env").write_text(
        "GEMINI_API_KEY=cwd-placeholder\nNEXO_AI_PROVIDER=auto\n", encoding="utf-8"
    )
    if external:
        (folder / ".env").write_text(
            "GEMINI_API_KEY=external-placeholder\nNEXO_AI_PROVIDER=auto\n",
            encoding="utf-8-sig",
        )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(paths.sys, "frozen", True, raising=False)
    monkeypatch.setattr(paths.sys, "executable", str(folder / "Nexo.exe"))
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("NEXO_AI_PROVIDER", "auto")
    monkeypatch.setenv("NEXO_AI_MODEL", "environment-model")
    settings = AISettings.from_environment()
    assert settings.cloud and settings.model == "environment-model"
    assert bool(
        settings.api_key == ("external-placeholder" if external else "cwd-placeholder")
    )
    assert (
        "placeholder" not in repr(settings)
        and "placeholder" not in settings.model_dump_json()
    )


def test_chat_is_simple_and_context_resets(qtbot, portfolio_investigation, tmp_path):
    from nexo.ui.pages.intelligence_page import IntelligencePage

    page = IntelligencePage(portfolio_investigation)
    qtbot.addWidget(page)
    page.resize(1100, 760)
    page.show()
    page.portfolio.setCurrentIndex(1)
    assert not page.tabs.tabBar().isVisible() and page.portfolio.isVisible()
    assert not page.context_dialog.isVisible() and page.method.currentData() == ""
    previous = page._conversation
    page.question.setPlainText("Devo comprar PETR4?")
    page.ask()
    qtbot.waitUntil(lambda: page._response is not None, timeout=5000)
    assert page.tabs.currentIndex() == 0 and page.report_button.isEnabled()
    assert "get_portfolio_snapshot" not in page.chat.toPlainText()
    page.portfolio.setCurrentIndex(2)
    assert page._conversation != previous and page._response is None
    assert not page.report_button.isEnabled()
    assert "Olá!" in page.chat.toPlainText()
    page.grab().save(str(tmp_path / "hotfix-chat.png"))
    page.runner.stop()
    page.runner.wait()
