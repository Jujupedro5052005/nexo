import csv
import io
import os
from datetime import date, datetime, timezone
from decimal import Decimal
from zipfile import ZipFile

import httpx
import pytest

from nexo.calculations.indicators.official import cross_check, official_basics
from nexo.domain.interfaces.market_data_provider import MarketDataUnavailableError
from nexo.domain.models.asset import Asset
from nexo.domain.models.fundamentals import CompanyFundamentals
from nexo.domain.models.official_data import CompanyIdentity, OfficialFinancialStatement
from nexo.infrastructure.market_data.adapters.cvm import (
    CompanyIdentityCache,
    CvmOfficialProvider,
)
from nexo.infrastructure.market_data.routing import RoutedFundamentalDataProvider

NOW = datetime(2026, 10, 7, tzinfo=timezone.utc)
A = Asset("ITSA4")
IDENTITY = CompanyIdentity(
    "ITSA4",
    "ITSA4",
    ("ITSA3", "ITSA4"),
    "ITAUSA S.A.",
    "ITAUSA",
    "7617",
    "61532644000115",
)


def csv_bytes(rows):
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]), delimiter=";")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("latin1")


def registry():
    return csv_bytes(
        [
            {
                "CNPJ_CIA": "61.532.644/0001-15",
                "CD_CVM": "07617",
                "DENOM_SOCIAL": "ITAUSA S.A.",
                "DENOM_COMERC": "ITAUSA",
                "SIT": "ATIVO",
                "CATEG_REG": "Categoria A",
                "DT_REG": "1977-07-20",
            }
        ]
    )


def account(
    account_code="1",
    account_name="Ativo Total",
    value="300",
    reference="2026-06-30",
    **extra,
):
    return {
        "CNPJ_CIA": "61.532.644/0001-15",
        "CD_CVM": "7617",
        "DT_REFER": reference,
        "VERSAO": "1",
        "ORDEM_EXERC": "ÚLTIMO",
        "MOEDA": "REAL",
        "ESCALA_MOEDA": "MIL",
        "CD_CONTA": account_code,
        "DS_CONTA": account_name,
        "VL_CONTA": value,
        "DT_INI_EXERC": "2026-01-01",
        "DT_FIM_EXERC": reference,
        **extra,
    }


def zipped(report="ITR", year=2026, files=None):
    stream = io.BytesIO()
    files = files or {f"{report.lower()}_cia_aberta_BPA_con_{year}.csv": [account()]}
    with ZipFile(stream, "w") as archive:
        for name, rows in files.items():
            archive.writestr(name, csv_bytes(rows))
    return stream.getvalue()


def provider(policy, tmp_path, payloads, resolve=lambda _: IDENTITY):
    calls = []

    def handler(request):
        calls.append(request.url.path)
        payload = payloads.get(request.url.path.rsplit("/", 1)[-1])
        return (
            httpx.Response(200, content=payload)
            if payload is not None
            else httpx.Response(404)
        )

    api = CvmOfficialProvider(
        policy,
        resolve,
        tmp_path / "cvm",
        now=lambda: NOW,
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    return api, calls


def test_cadastro_exact_keys_dataset_cache_shared_across_companies(policy, tmp_path):
    api, calls = provider(policy, tmp_path, {"cad_cia_aberta.csv": registry()})
    company = api.get_company(A)
    assert company.cvm_code == "7617" and company.cnpj == "61532644000115"
    assert (
        company.corporate_name == "ITAUSA S.A."
        and company.registration_date == date(1977, 7, 20)
    )
    assert company.source == "CVM"
    api.get_company(A)
    api.get_company(Asset("ITSA3"))
    assert len(calls) == policy.usage.count("CVM") == 1
    assert "cad_cia_aberta.csv" in api.cache_updates()[0]


def test_no_identity_mapping_does_not_download_or_match_names(policy, tmp_path):
    def unresolved(_):
        raise MarketDataUnavailableError("bolsai not configured")

    api, calls = provider(policy, tmp_path, {}, resolve=unresolved)
    with pytest.raises(
        MarketDataUnavailableError, match="Identidade oficial não resolvida"
    ):
        api.get_company(A)
    assert not calls and policy.usage.count("CVM") == 0


def test_conflicting_cnpj_and_cvm_never_returns_similar_company(policy, tmp_path):
    wrong = CompanyIdentity(
        "ITSA4", "ITSA4", ("ITSA4",), "ITAUSA", "", "1234", IDENTITY.cnpj
    )
    api, _ = provider(
        policy, tmp_path, {"cad_cia_aberta.csv": registry()}, resolve=lambda _: wrong
    )
    with pytest.raises(MarketDataUnavailableError, match="não localizada"):
        api.get_company(A)


@pytest.mark.parametrize("report,year", [("DFP", 2026), ("DFP", 2025), ("ITR", 2026)])
def test_dfp_itr_ingestion_scale_source_dates_and_zip_cache(
    policy, tmp_path, report, year
):
    filename = f"{report.lower()}_cia_aberta_{year}.zip"
    api, calls = provider(policy, tmp_path, {filename: zipped(report, year)})
    rows = api.ingest(IDENTITY, report, year)
    assert rows[0].value == 300000 and rows[0].consolidated
    assert rows[0].report_type == report and rows[0].source == "CVM"
    assert rows[0].reference_date == date(2026, 6, 30)
    api.ingest(IDENTITY, report, year)
    assert len(calls) == 1 and (api.cache_dir / filename).exists()


def test_consolidated_priority_individual_fallback_version_period_and_no_sum(
    policy, tmp_path
):
    files = {
        "itr_cia_aberta_BPA_con_2026.csv": [
            account(value="100"),
            account(value="300", VERSAO="2"),
            account(value="999", VERSAO="2", ORDEM_EXERC="PENÚLTIMO"),
        ],
        "itr_cia_aberta_BPA_ind_2026.csv": [account(value="200", VERSAO="2")],
        "itr_cia_aberta_BPP_ind_2026.csv": [
            account("2.03", "Patrimônio Líquido", "50", VERSAO="2")
        ],
        "itr_cia_aberta_DRE_con_2026.csv": [
            account("3.01", "Receita de Venda de Bens e/ou Serviços", "80", VERSAO="2"),
            account(
                "3.01",
                "Receita de Venda de Bens e/ou Serviços",
                "40",
                VERSAO="2",
                DT_INI_EXERC="2026-04-01",
            ),
        ],
        "../../outside.csv": [account(value="999")],
    }
    api, _ = provider(
        policy, tmp_path, {"itr_cia_aberta_2026.zip": zipped(files=files)}
    )
    rows = api.ingest(IDENTITY, "ITR", 2026)
    basics = official_basics(rows)
    assert basics == {
        "total_assets": Decimal(300000),
        "equity": Decimal(50000),
        "revenue": Decimal(80000),
    }
    assert next(r for r in rows if r.statement_type == "BPP").consolidated is False
    assert len(rows) == 3 and not (tmp_path / "outside.csv").exists()


@pytest.mark.parametrize(
    "report,year", [("ITR", 2025), ("DFP", 2024), ("DFP", 2010), ("IPE", 2026)]
)
def test_no_historical_bulk_download(policy, tmp_path, report, year):
    api, calls = provider(policy, tmp_path, {})
    with pytest.raises(MarketDataUnavailableError, match="fora do escopo"):
        api.ingest(IDENTITY, report, year)
    assert not calls


def test_latest_statements_can_use_current_itr_previous_dfp_and_cache(policy, tmp_path):
    policy.usage.budgets["CVM"] = 4
    api, calls = provider(
        policy,
        tmp_path,
        {
            "cad_cia_aberta.csv": registry(),
            "itr_cia_aberta_2026.zip": zipped(),
            "dfp_cia_aberta_2026.zip": zipped(
                "DFP",
                2026,
                {"dfp_cia_aberta_BPA_con_2026.csv": [account(CD_CVM="9999")]},
            ),
            "dfp_cia_aberta_2025.zip": zipped("DFP", 2025),
        },
    )
    rows = api.get_statements(A)
    assert {r.report_type for r in rows} == {"ITR", "DFP"}
    assert len(calls) == 4
    api.get_statements(A)
    assert len(calls) == 4


def test_cvm_budget_two_returns_available_itr_without_exceeding_budget(
    policy, tmp_path
):
    api, calls = provider(
        policy,
        tmp_path,
        {"cad_cia_aberta.csv": registry(), "itr_cia_aberta_2026.zip": zipped()},
    )
    rows = api.get_statements(A)
    assert {r.report_type for r in rows} == {"ITR"} and len(calls) == 2


def test_dataset_ttl_24h_and_expired_cache_does_not_hide_failed_refresh(
    policy, tmp_path
):
    api, calls = provider(policy, tmp_path, {"cad_cia_aberta.csv": registry()})
    api.get_company(A)
    path = api.cache_dir / "cad_cia_aberta.csv"
    os.utime(path, (NOW.timestamp(), NOW.timestamp()))
    api.policy.invalidate()
    api.get_company(A)
    assert len(calls) == 1
    os.utime(path, (NOW.timestamp() - 86400, NOW.timestamp() - 86400))
    api.policy.invalidate()
    api.get_company(A)
    assert len(calls) == 2


def test_identity_disk_bridge_survives_restart_without_key(tmp_path):
    cache = CompanyIdentityCache(tmp_path / "identities", lambda _: IDENTITY)
    assert cache.resolve(A) == IDENTITY

    def no_network(_):
        raise AssertionError("cached identity must be reused")

    reopened = CompanyIdentityCache(tmp_path / "identities", no_network)
    assert reopened.resolve(A) == IDENTITY
    assert "cnpj" in (tmp_path / "identities/ITSA4.json").read_text()


def test_official_fundamental_fallback_keeps_source_and_no_aggregation(
    policy, tmp_path
):
    api, calls = provider(
        policy,
        tmp_path,
        {"cad_cia_aberta.csv": registry(), "itr_cia_aberta_2026.zip": zipped()},
    )

    class Unavailable:
        def get_fundamentals(self, asset):
            raise MarketDataUnavailableError("offline")

    router = RoutedFundamentalDataProvider(Unavailable(), api, policy)
    f = router.get_fundamentals(A)
    assert f.source == "CVM" and f.total_assets == 300000 and f.pe is f.eps is None
    assert router.get_fundamentals(A) == f and len(calls) == 2


def test_cross_check_only_identifiable_accounts_same_date_no_ttm_guess():
    row = OfficialFinancialStatement(
        "7617",
        IDENTITY.cnpj,
        date(2026, 6, 30),
        "ITR",
        "BPA",
        "1",
        "Ativo Total",
        Decimal(300),
        True,
    )
    f = CompanyFundamentals(
        A,
        NOW,
        reference_date=row.reference_date,
        total_assets=Decimal(350),
        source="bolsai",
    )
    assert "50" in cross_check(f, (row,))[0] and f.total_assets == 350
    ambiguous = OfficialFinancialStatement(
        "7617",
        IDENTITY.cnpj,
        row.reference_date,
        "ITR",
        "BPA",
        "1",
        "Conta personalizada",
        Decimal(999),
        True,
    )
    assert not cross_check(f, (ambiguous,))
    assert not cross_check(
        CompanyFundamentals(A, NOW, total_assets=Decimal(350)), (row,)
    )


def test_dfp_missing_current_zip_falls_back_only_to_previous_year(policy, tmp_path):
    policy.usage.budgets["CVM"] = 4
    api, calls = provider(
        policy,
        tmp_path,
        {
            "cad_cia_aberta.csv": registry(),
            "itr_cia_aberta_2026.zip": zipped(),
            "dfp_cia_aberta_2025.zip": zipped("DFP", 2025),
        },
    )
    rows = api.get_statements(A)
    assert {r.report_type for r in rows} == {"ITR", "DFP"} and len(calls) == 4
    assert not any("2024" in path for path in calls)


def test_explicit_official_retry_fills_dfp_without_redownloading_valid_registry_itr(
    policy, tmp_path
):
    from nexo.infrastructure.market_data.policy import explicit_refresh

    api, calls = provider(
        policy,
        tmp_path,
        {
            "cad_cia_aberta.csv": registry(),
            "itr_cia_aberta_2026.zip": zipped(),
            "dfp_cia_aberta_2026.zip": zipped("DFP", 2026),
        },
    )
    assert {r.report_type for r in api.get_statements(A)} == {"ITR"}
    assert len(calls) == 2
    with explicit_refresh():
        api.invalidate(A)
        rows = api.get_statements(A)
    assert {r.report_type for r in rows} == {"ITR", "DFP"}
    assert len(calls) == 3 and sum("itr" in p for p in calls) == 1


def test_official_currency_scale_preserves_account_precision(policy, tmp_path):
    from decimal import localcontext

    archive = zipped(
        files={
            "itr_cia_aberta_BPA_con_2026.csv": [account(value="300000000.123456789")]
        }
    )
    api, _ = provider(policy, tmp_path, {"itr_cia_aberta_2026.zip": archive})
    with localcontext() as context:
        context.prec = 3
        assert api.ingest(IDENTITY, "ITR", 2026)[0].value == Decimal(
            "300000000123.456789"
        )
