from datetime import timedelta
from decimal import Decimal

import pytest
from PySide6.QtCore import Qt

from nexo.application.intelligence.deep_analysis import compact_report
from nexo.calculations.risk.correlation import aligned_correlation
from nexo.calculations.valuation.bank import bank_residual_value
from nexo.domain.models.fundamentals import (
    CashDividend,
    CompanyFundamentals,
    DividendSummary,
)
from nexo.domain.models.intelligence import (
    AnalysisRequest,
    IntelligenceError,
    utc_now,
)
from nexo.domain.models.market_data import HistoricalPrice, PriceHistory, Quote
from nexo.infrastructure.intelligence.knowledge import (
    LocalKnowledgeRetriever,
    load_canonical_library,
)
from nexo.ui.pages.intelligence_page import IntelligencePage


@pytest.fixture(name="investigation")
def investigation_data(workspace):
    now = utc_now()
    tools = workspace.orchestrator.tools
    tools.quote.execute = lambda a: Quote(
        a, Decimal(18), "BRL", a.symbol, now, now, source="synthetic-fixture"
    )
    tools.fundamentals.get_fundamentals = lambda a: CompanyFundamentals(
        a,
        now,
        eps=Decimal(3),
        bvps=Decimal(20),
        roe=Decimal("0.18"),
        reference_date=now.date(),
        source="synthetic-fixture",
    )
    tools.dividends.get_dividends = lambda a, start, end: DividendSummary(
        a,
        (
            CashDividend(
                end,
                Decimal(3),
                "DIVIDENDO",
                verified=True,
                asset=a,
                source="synthetic-fixture",
            ),
        ),
        start,
        end,
        now,
        source="synthetic-fixture",
    )
    tools.history.execute = lambda a, period: PriceHistory(
        a,
        tuple(
            HistoricalPrice(now - timedelta(days=40 - i), Decimal(20 + i + i % 3))
            for i in range(30)
        ),
        period,
        now,
        source="synthetic-fixture",
        split_adjusted=True,
    )
    return workspace


def request(**values):
    return AnalysisRequest(
        question="Qual é o preço teto de ITUB4?",
        symbol="ITUB4",
        analysis_mode="deep",
        **values,
    )


def test_bank_known_values_and_limits():
    assert (
        bank_residual_value(
            Decimal(20), Decimal("0.14"), Decimal("0.14"), Decimal("0.03")
        )
        == 20
    )
    value = bank_residual_value(
        Decimal(20), Decimal("0.18"), Decimal("0.14"), Decimal("0.03")
    )
    assert abs(value - Decimal("27.27272727272727")) < Decimal("0.000000000001")
    for values in (
        ("20", ".18", ".03", ".03"),
        ("-1", ".18", ".14", ".03"),
        ("20", ".01", ".14", ".03"),
        ("NaN", ".18", ".14", ".03"),
        ("20", ".18", "1e-999999999", "0"),
    ):
        with pytest.raises(ValueError):
            bank_residual_value(*(Decimal(v) for v in values))


def test_deep_asset_generates_audited_scenarios_without_manual_parameters(
    investigation,
):
    response = investigation.ask(request())
    asset = response.report["assets"][0]
    assert asset["symbol"] == "ITUB4" and asset["sector"] == "Bancos"
    assert len(asset["scenarios"]) == 3
    assert [s["label"] for s in asset["scenarios"]] == [
        "conservador",
        "base",
        "otimista",
    ]
    assert asset["verdict"] == "Favorável no cenário estimado"
    assert asset["scenarios"][1]["method"] == "bank_residual"
    assert all(s["assumption_kind"] == "estimated" for s in asset["scenarios"])
    assert asset["risk"]["observations"] == 30
    assert asset["quote"]["market_time"] != ""
    assert "fundamentals" in compact_report(response.report)["assets"][0]


def test_estimates_can_be_disabled_and_no_fake_zero(investigation):
    result = investigation.ask(request(allow_estimates=False))
    assert result.report["assets"][0]["scenarios"] == []
    investigation.orchestrator.tools.fundamentals.get_fundamentals = lambda a: (
        CompanyFundamentals(a, utc_now(), source="fixture")
    )
    investigation.orchestrator.deep._cache.clear()
    investigation.orchestrator.tools.dividends.get_dividends = lambda a, s, e: (
        DividendSummary(a, (), s, e, utc_now())
    )
    result = investigation.ask(request())
    assert result.report["assets"][0]["scenarios"] == []
    assert "Dados insuficientes" in result.report["assets"][0]["verdict"]


def test_follow_up_margin_and_conversation_scope(investigation):
    first = investigation.ask(request())
    base1 = first.report["assets"][0]["scenarios"][1]
    second = investigation.ask(
        AnalysisRequest(question="Refaça usando uma margem de segurança de 25%.")
    )
    base2 = second.report["assets"][0]["scenarios"][1]
    assert base2["safety_discount"] == "0.25"
    assert Decimal(base2["ceiling_price"]) < Decimal(base1["ceiling_price"])
    assert second.report["assets"][0]["symbol"] == "ITUB4"
    assert (
        investigation.storage.get_state("conversation:default")["analysis_mode"]
        == "deep"
    )


def test_natural_ticker_question_and_followup_retain_asset_scope(investigation):
    first = investigation.ask(AnalysisRequest(question="Qual é o preço teto de ITUB4?"))
    assert first.report["assets"][0]["scenarios"][1]["method"] == "bank_residual"
    revised = investigation.ask(
        AnalysisRequest(question="Refaça com margem de segurança de 25%.")
    )
    asset = revised.report["assets"][0]
    assert asset["symbol"] == "ITUB4"
    assert asset["scenarios"][1]["safety_discount"] == "0.25"


def test_comparison_followup_retains_both_tickers(investigation):
    investigation.ask(AnalysisRequest(question="Compare PETR4 e PRIO3."))
    revised = investigation.ask(
        AnalysisRequest(question="Compare o resultado com outra metodologia.")
    )
    assert {a["symbol"] for a in revised.report["assets"]} == {"PETR4", "PRIO3"}
    assert all(a["cross_checks"] for a in revised.report["assets"])


def test_changing_selected_asset_does_not_inherit_previous_focus(investigation):
    investigation.ask(AnalysisRequest(question="Qual é o preço teto de ITUB4?"))
    changed = investigation.ask(
        AnalysisRequest(
            question="Refaça a análise anterior.", symbol="PETR4", analysis_mode="deep"
        )
    )
    assert [a["symbol"] for a in changed.report["assets"]] == ["PETR4"]


@pytest.mark.parametrize(
    "question",
    [
        "Compare PETR4 e PRIO3.",
        "Qual empresa parece mais atrativa pelo valuation atual? PETR4 ou PRIO3?",
    ],
)
def test_comparison_inspects_both_assets_instead_of_quotes_only(
    investigation, question
):
    result = investigation.ask(AnalysisRequest(question=question))
    assert {a["symbol"] for a in result.report["assets"]} == {"PETR4", "PRIO3"}
    assert all(
        a["fundamentals"] and a["history"] and len(a["scenarios"]) == 3
        for a in result.report["assets"]
    )


def test_conceptual_question_does_not_query_selected_asset(investigation):
    def forbidden(*a, **kw):
        pytest.fail("Pergunta conceitual não deve consultar mercado")

    investigation.orchestrator.tools.quote.execute = forbidden
    response = investigation.ask(
        AnalysisRequest(
            question="Explique uma metodologia de valuation.", symbol="ITUB4"
        )
    )
    assert response.evidence == ()


def test_conceptual_question_rejects_unnecessary_market_plan(investigation):
    from nexo.domain.models.intelligence import ToolCall

    investigation.orchestrator.cloud = True
    investigation.orchestrator.provider.plan = lambda *args: (
        ToolCall(name="get_asset_quote", arguments={"symbol": "ITUB4"}),
    )
    investigation.orchestrator.tools.quote.execute = lambda *args: pytest.fail(
        "Unnecessary quote"
    )
    result = investigation.ask(
        AnalysisRequest(question="Explique Gordon.", symbol="ITUB4", allow_cloud=True)
    )
    assert result.evidence == ()


def test_library_falls_back_to_installed_wheel_data(storage, monkeypatch, tmp_path):
    from nexo.infrastructure.intelligence import knowledge

    root = tmp_path / "share" / "nexo" / "knowledge" / "foundations"
    root.mkdir(parents=True)
    (root / "chapter.md").write_text(
        "# Referência instalada\n\nConteúdo autorizado.", encoding="utf-8"
    )
    monkeypatch.setattr(
        knowledge,
        "__file__",
        str(tmp_path / "installed" / "src" / "nexo" / "infra" / "knowledge.py"),
    )
    monkeypatch.setattr(knowledge.sys, "prefix", str(tmp_path))
    assert load_canonical_library(storage) == 1
    assert storage.documents()[0]["canonical_id"] == "foundations/chapter.md"


def test_calls_and_cache_are_bounded_and_source_errors_remain_partial(investigation):
    first = investigation.ask(request())
    second = investigation.ask(request())
    assert first.report["calls"] == 4
    assert second.report["calls"] == 0
    investigation.orchestrator.deep.max_assets = 0
    with pytest.raises(IntelligenceError, match="limitada"):
        investigation.ask(request())


def test_unclassified_asset_is_not_silently_a_fii(investigation):
    result = investigation.ask(
        AnalysisRequest(
            question="Analise ABCD11", symbol="ABCD11", analysis_mode="deep"
        )
    )
    asset = result.report["assets"][0]
    assert asset["asset_type"] == "unknown"
    assert asset["scenarios"] == []


def test_pearson_alignment_and_constant_series():
    left = {f"2026-01-{i + 1:02}": Decimal(20 + i + i % 3) for i in range(25)}
    right = {k: v * 2 for k, v in left.items()}
    assert abs(aligned_correlation(left, right) - 1) < Decimal("1e-30")
    assert aligned_correlation({"a": Decimal(1)}, {"a": Decimal(1)}) is None
    constant = {k: Decimal(1) for k in left}
    assert aligned_correlation(left, constant) is None
    right.pop(next(iter(right)))
    assert aligned_correlation(left, right) is not None


def test_canonical_library_is_populated_deduplicated_and_searchable(storage):
    assert load_canonical_library(storage) == 15
    assert load_canonical_library(storage) == 15
    documents = [d for d in storage.documents() if d.get("canonical_id")]
    assert len(documents) == 15
    assert all(
        d["active"] and d["authorized"] and "Referências" in d["text"]
        for d in documents
    )
    hits = LocalKnowledgeRetriever(storage).search("Gordon dividendos crescimento Ke")
    assert hits and all(h.sources[0].uri.startswith("nexo://knowledge/") for h in hits)


def test_export_is_human_report_and_diagnostics_are_separate(investigation, tmp_path):
    result = investigation.ask(request())
    md, js = tmp_path / "report.md", tmp_path / "diagnostic.json"
    investigation.export(md, result)
    investigation.export_diagnostics(js, result)
    text = md.read_text(encoding="utf-8")
    assert "```json" not in text
    assert "Preço teto" in text and "bank_residual" in text
    assert "volatilidade anualizada" in text and "drawdown máximo" in text
    assert "Verificação alternativa" in text and "não é mediana de pares" in text
    assert '"report"' in js.read_text(encoding="utf-8")


def test_modern_chat_hides_raw_json_and_context_and_enter_submits(qtbot, investigation):
    page = IntelligencePage(investigation)
    qtbot.addWidget(page)
    page.resize(1180, 760)
    page.show()
    assert page.context_drawer.isHidden()
    assert (
        page.settings_text.isHidden()
        and page.method_preview.isHidden()
        and page.evidence.isHidden()
    )
    assert page.tabs.tabText(0) == "Copiloto"
    page.question.setPlainText("Olá")
    qtbot.keyClick(page.question, Qt.Key.Key_Return, Qt.KeyboardModifier.ShiftModifier)
    assert "\n" in page.question.toPlainText()
    qtbot.keyClick(page.question, Qt.Key.Key_Return)
    qtbot.waitUntil(lambda: page._response is not None)
    page.runner.stop()
    page.runner.wait()
