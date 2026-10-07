"""Official CVM CSV/ZIP ingestion. Never calls an unofficial statements API."""

import csv
import io
import json
import re
from collections.abc import Callable
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from threading import RLock
from typing import Any
from zipfile import BadZipFile, ZipFile

import httpx

from nexo.calculations.precision import financial_context
from nexo.domain.interfaces.market_data_provider import (
    AssetNotFoundError,
    MarketDataError,
    MarketDataUnavailableError,
)
from nexo.domain.interfaces.official_data_provider import (
    OfficialCompanyDataProvider,
    OfficialFinancialStatementProvider,
)
from nexo.domain.models.asset import Asset
from nexo.domain.models.official_data import (
    CompanyIdentity,
    OfficialCompany,
    OfficialFinancialStatement,
)
from nexo.infrastructure.market_data.policy import ProviderPolicy

BASE_URL = "https://dados.cvm.gov.br/dados/cia_aberta"


def digits(value: str) -> str:
    return "".join(c for c in value if c.isdigit())


def code(value: str) -> str:
    return str(int(value))


class CvmOfficialProvider(
    OfficialCompanyDataProvider, OfficialFinancialStatementProvider
):
    def __init__(
        self,
        policy: ProviderPolicy,
        resolve_identity: Callable[[Asset], CompanyIdentity],
        cache_dir: Path,
        *,
        client: httpx.Client | None = None,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self.policy, self.resolve_identity, self.cache_dir = (
            policy,
            resolve_identity,
            cache_dir,
        )
        self._owns_client = client is None
        self.client = client or httpx.Client(timeout=30, follow_redirects=False)
        self.now = now or (lambda: datetime.now(timezone.utc))
        self._lock = RLock()

    def close(self) -> None:
        if self._owns_client:
            self.client.close()

    def invalidate(self, asset: Asset) -> None:
        self.policy.invalidate_capabilities("CVM", ("statements", "fundamentals"))

    def cache_updates(self) -> tuple[str, ...]:
        if not self.cache_dir.exists():
            return ()
        return tuple(
            f"{p.name}: {datetime.fromtimestamp(p.stat().st_mtime, timezone.utc).isoformat(timespec='seconds')}"
            for p in sorted(self.cache_dir.iterdir())
            if p.suffix in {".zip", ".csv"}
        )

    def _dataset(self, filename: str, url: str, operation: str) -> Path:
        # Dataset lock coalesces downloads shared by different company requests.
        with self._lock:
            path = self.cache_dir / filename
            if path.exists() and self.now().timestamp() - path.stat().st_mtime < 86400:
                return path
            self.policy.usage.reserve("CVM", operation)
            try:
                response = self.client.get(url)
                if response.status_code == 404:
                    raise AssetNotFoundError(
                        "Dataset CVM ainda não publicado para este ano."
                    )
                response.raise_for_status()
                if filename.endswith(".zip"):
                    with ZipFile(io.BytesIO(response.content)) as archive:
                        if archive.testzip() is not None:
                            raise BadZipFile("Invalid ZIP")
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                temporary = path.with_suffix(".tmp")
                temporary.write_bytes(response.content)
                temporary.replace(path)
                return path
            except (httpx.HTTPError, OSError, BadZipFile):
                raise MarketDataUnavailableError(
                    "Dataset oficial CVM indisponível; cache preservado."
                ) from None

    def _identity(self, asset: Asset) -> CompanyIdentity:
        try:
            identity = self.resolve_identity(asset)
            if not identity.cvm_code or len(digits(identity.cnpj)) != 14:
                raise ValueError("Incomplete identity")
            return identity
        except (MarketDataError, ValueError):
            raise MarketDataUnavailableError(
                "Identidade oficial não resolvida; mapeamento ticker/CNPJ/CVM necessário."
            ) from None

    def get_company(self, asset: Asset) -> OfficialCompany:
        identity = self._identity(asset)

        def fetch() -> OfficialCompany:
            path = self._dataset(
                "cad_cia_aberta.csv",
                BASE_URL + "/cad/DADOS/cad_cia_aberta.csv",
                "registry",
            )
            try:
                with path.open(encoding="latin1", newline="") as stream:
                    for row in csv.DictReader(stream, delimiter=";"):
                        if digits(row["CNPJ_CIA"]) == digits(identity.cnpj) and code(
                            row["CD_CVM"]
                        ) == code(identity.cvm_code):
                            return OfficialCompany(
                                digits(row["CNPJ_CIA"]),
                                code(row["CD_CVM"]),
                                row["DENOM_SOCIAL"],
                                row.get("DENOM_COMERC", ""),
                                row.get("SIT", ""),
                                row.get("CATEG_REG", ""),
                                date.fromisoformat(row["DT_REG"])
                                if row.get("DT_REG")
                                else None,
                            )
            except (KeyError, ValueError, OSError):
                raise MarketDataUnavailableError("Cadastro CVM inválido.") from None
            raise MarketDataUnavailableError(
                "Identidade não localizada no cadastro oficial CVM."
            )

        return self.policy.call(
            "CVM", "registry", (identity.cvm_code, identity.cnpj), fetch
        )

    def ingest(
        self, identity: CompanyIdentity, report_type: str, year: int
    ) -> tuple[OfficialFinancialStatement, ...]:
        current = self.now().year
        if (
            report_type not in {"DFP", "ITR"}
            or year not in {current, current - 1}
            or (report_type == "ITR" and year != current)
        ):
            raise MarketDataUnavailableError(
                "CVM: período fora do escopo atual/anterior."
            )
        prefix = report_type.lower()
        filename = f"{prefix}_cia_aberta_{year}.zip"
        path = self._dataset(
            filename, f"{BASE_URL}/doc/{prefix}/DADOS/{filename}", report_type
        )
        rows: list[OfficialFinancialStatement] = []
        try:
            with ZipFile(path) as archive:
                for entry in archive.infolist():
                    # Match exact statement files, not metadata, parecer or arbitrary ZIP paths.
                    match = re.fullmatch(
                        rf"{prefix}_cia_aberta_(BPA|BPP|DRE|DFC_MD|DFC_MI|DVA|DMPL|DRA)_(con|ind)_{year}\.csv",
                        entry.filename,
                    )
                    if match is None:
                        continue
                    with archive.open(entry) as binary:  # noqa: SIM117 -- streaming CSV wrapper owns the binary stream.
                        with io.TextIOWrapper(
                            binary, encoding="latin1", newline=""
                        ) as stream:
                            for row in csv.DictReader(stream, delimiter=";"):
                                if code(row["CD_CVM"]) != code(
                                    identity.cvm_code
                                ) or digits(row["CNPJ_CIA"]) != digits(identity.cnpj):
                                    continue
                                if row.get("ORDEM_EXERC", "ÚLTIMO").upper() not in {
                                    "ÚLTIMO",
                                    "ULTIMO",
                                }:
                                    continue
                                if row.get("MOEDA", "REAL").upper() not in {
                                    "REAL",
                                    "REAIS",
                                    "BRL",
                                }:
                                    continue
                                scale = row.get("ESCALA_MOEDA", "UNIDADE").upper()
                                if scale not in {"MIL", "UNIDADE"}:
                                    continue
                                amount = Decimal(row["VL_CONTA"].replace(",", "."))
                                if not amount.is_finite():
                                    raise ValueError("Nonfinite account")
                                rows.append(
                                    OfficialFinancialStatement(
                                        code(row["CD_CVM"]),
                                        digits(row["CNPJ_CIA"]),
                                        date.fromisoformat(row["DT_REFER"]),
                                        report_type,
                                        match[1],
                                        row["CD_CONTA"],
                                        row["DS_CONTA"],
                                        amount.scaleb(
                                            3, context=financial_context([amount])
                                        )
                                        if scale == "MIL"
                                        else amount,
                                        match[2] == "con",
                                        period_start=date.fromisoformat(
                                            row["DT_INI_EXERC"]
                                        )
                                        if row.get("DT_INI_EXERC")
                                        else None,
                                        period_end=date.fromisoformat(
                                            row["DT_FIM_EXERC"]
                                        )
                                        if row.get("DT_FIM_EXERC")
                                        else None,
                                        version=int(row.get("VERSAO", "1")),
                                    )
                                )
            return self.select(rows)
        except (KeyError, ValueError, ArithmeticError, OSError, BadZipFile):
            raise MarketDataUnavailableError("Demonstrações CVM inválidas.") from None

    @staticmethod
    def select(
        rows: list[OfficialFinancialStatement],
    ) -> tuple[OfficialFinancialStatement, ...]:
        if not rows:
            return ()
        latest = max(r.reference_date for r in rows)
        rows = [r for r in rows if r.reference_date == latest]
        version = max(r.version for r in rows)
        rows = [r for r in rows if r.version == version]
        # Prefer consolidated independently for each statement type; never sum scopes.
        consolidated = {r.statement_type for r in rows if r.consolidated}
        rows = [
            r for r in rows if r.consolidated or r.statement_type not in consolidated
        ]
        selected: dict[tuple[str, str], OfficialFinancialStatement] = {}
        for row in rows:
            key = row.statement_type, row.account_code
            previous = selected.get(key)
            # For multiple current DRE periods, prefer YTD (earliest start).
            if previous is None or (row.period_start or date.max) < (
                previous.period_start or date.max
            ):
                selected[key] = row
        return tuple(selected[k] for k in sorted(selected))

    def get_statements(self, asset: Asset) -> tuple[OfficialFinancialStatement, ...]:
        identity = self._identity(asset)

        def fetch() -> tuple[OfficialFinancialStatement, ...]:
            self.get_company(asset)  # Verify both keys against the official registry.
            records: list[OfficialFinancialStatement] = []
            errors: list[MarketDataError] = []
            for report in ("ITR", "DFP"):
                try:
                    try:
                        result = self.ingest(identity, report, self.now().year)
                    except AssetNotFoundError:
                        if report != "DFP":
                            raise
                        result = self.ingest(identity, report, self.now().year - 1)
                    if report == "DFP" and not result:
                        result = self.ingest(identity, report, self.now().year - 1)
                    records.extend(result)
                except MarketDataError as error:
                    errors.append(error)
            if not records and errors:
                raise errors[0]
            if not records:
                raise MarketDataUnavailableError(
                    "Sem demonstrações recentes para a companhia."
                )
            return tuple(records)

        return self.policy.call(
            "CVM", "statements", (identity.cvm_code, identity.cnpj), fetch
        )


class CompanyIdentityCache:
    """Seven-day disk bridge; survives restarts without credentials in its payload."""

    def __init__(
        self, directory: Path, fetch: Callable[[Asset], CompanyIdentity]
    ) -> None:
        self.directory, self.fetch = directory, fetch
        self._lock = RLock()

    def resolve(self, asset: Asset) -> CompanyIdentity:
        with self._lock:
            path = self.directory / (asset.symbol + ".json")
            if (
                path.exists()
                and datetime.now(timezone.utc).timestamp() - path.stat().st_mtime
                < 604800
            ):
                try:
                    data: dict[str, Any] = json.loads(path.read_text(encoding="utf8"))
                    data["tickers"] = tuple(data["tickers"])
                    identity = CompanyIdentity(**data)
                    if (
                        identity.queried_ticker == asset.symbol
                        and asset.symbol in identity.tickers
                    ):
                        return identity
                except (OSError, KeyError, TypeError, ValueError):
                    pass
            identity = self.fetch(asset)
            from dataclasses import asdict

            self.directory.mkdir(parents=True, exist_ok=True)
            temporary = path.with_suffix(".tmp")
            temporary.write_text(
                json.dumps(asdict(identity), ensure_ascii=False), encoding="utf8"
            )
            temporary.replace(path)
            return identity
