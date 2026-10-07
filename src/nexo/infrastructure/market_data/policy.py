"""Shared TTL/coalescing, capability health and persistent local request accounting."""

import json
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
from pathlib import Path
from threading import Condition, RLock
from time import monotonic
from typing import Any, TypeVar, cast

from nexo.domain.interfaces.market_data_provider import (
    MarketCredentialsRequiredError,
    MarketDataError,
    MarketDataUnavailableError,
    MarketOfflineError,
    MarketPlanAccessError,
    MarketRateLimitError,
)
from nexo.domain.models.provider_health import ProviderHealth

T = TypeVar("T")
TTL = {
    ("brapi", "quote"): 60,
    ("brapi", "search"): 900,
    ("brapi", "history"): 1800,
    ("brapi", "fundamentals"): 43200,
    ("brapi", "dividends"): 43200,
    ("bolsai", "quote"): 21600,
    ("bolsai", "search"): 900,
    ("bolsai", "company"): 604800,
    ("bolsai", "fundamentals"): 43200,
    ("bolsai", "actions"): 43200,
    ("Yahoo Finance", "dividends"): 43200,
    ("Yahoo Finance", "history"): 3600,
    ("Yahoo Finance", "actions"): 43200,
    ("CVM", "registry"): 86400,
    ("CVM", "statements"): 86400,
    ("CVM", "fundamentals"): 86400,
}
_explicit: ContextVar[bool] = ContextVar("provider_explicit_refresh", default=False)


@contextmanager
def explicit_refresh() -> Iterator[None]:
    token = _explicit.set(True)
    try:
        yield
    finally:
        _explicit.reset(token)


class ProviderUsage:
    """Counts attempted remote operations, never official quota nor cache hits.

    One local writer process is assumed, matching the ledger's desktop lifecycle.
    Threads reserve under a lock and atomically replace the file before network I/O.
    """

    def __init__(
        self,
        path: Path,
        budgets: dict[str, int],
        *,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self.path, self.budgets = path, budgets
        self._now = now or (lambda: datetime.now(timezone.utc))
        self._lock = RLock()

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"date": self.today(), "usage": {}}
        try:
            data = json.loads(self.path.read_text(encoding="utf8"))
            if not isinstance(data, dict) or not isinstance(data.get("usage"), dict):
                raise TypeError("Invalid usage file")
            if data.get("date") != self.today():
                return {"date": self.today(), "usage": {}}
            for provider, operations in data["usage"].items():
                if (
                    provider not in self.budgets
                    or not isinstance(operations, dict)
                    or any(type(n) is not int or n < 0 for n in operations.values())
                ):
                    raise TypeError("Invalid local counter")
            return data
        except (OSError, ValueError, TypeError):
            raise MarketDataUnavailableError(
                "Contador local inválido; consulta remota suspensa."
            ) from None

    def today(self) -> str:
        return self._now().astimezone(timezone.utc).date().isoformat()

    def count(self, provider: str) -> int:
        with self._lock:
            return sum(int(n) for n in self._read()["usage"].get(provider, {}).values())

    def reserve(self, provider: str, operation: str) -> None:
        with self._lock:
            data = self._read()
            operations = data["usage"].setdefault(provider, {})
            if (
                sum(operations.values()) >= self.budgets[provider]
                and not _explicit.get()
            ):
                raise MarketRateLimitError(
                    "Budget local atingido; atualização explícita necessária."
                )
            operations[operation] = operations.get(operation, 0) + 1
            try:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                temporary = self.path.with_suffix(".tmp")
                temporary.write_text(json.dumps(data, indent=2), encoding="utf8")
                temporary.replace(self.path)
            except OSError:
                raise MarketDataUnavailableError(
                    "Não foi possível persistir o consumo local."
                ) from None


class ProviderPolicy:
    def __init__(
        self, usage: ProviderUsage, *, clock: Callable[[], float] = monotonic
    ) -> None:
        self.usage, self.clock = usage, clock
        self._condition = Condition()
        self._cache: dict[tuple[Any, ...], tuple[float, Any]] = {}
        self._pending: set[tuple[Any, ...]] = set()
        self._routes: set[tuple[Any, ...]] = set()
        self._negative: dict[tuple[str, str], float] = {}
        self._states: dict[tuple[str, str], str] = {}
        self._hits: dict[str, int] = {}
        self._misses: dict[str, int] = {}
        self.remaining: dict[str, int] = {}
        self._quota_dates: dict[str, str] = {}
        self._epoch = 0

    def update_quota(self, provider: str, remaining: int) -> None:
        with self._condition:
            self.remaining[provider] = remaining
            self._quota_dates[provider] = self.usage.today()

    def quota_remaining(self, provider: str) -> int | None:
        with self._condition:
            if (
                self._quota_dates.get(provider, self.usage.today())
                != self.usage.today()
            ):
                self.remaining.pop(provider, None)
            return self.remaining.get(provider)

    def invalidate(self, asset: Any = None) -> None:
        with self._condition:
            self._epoch += 1
            self._cache = {
                k: v
                for k, v in self._cache.items()
                if asset is not None and asset not in k[2:]
            }

    def cached(self, provider: str, capability: str, key: tuple[Any, ...]) -> Any:
        with self._condition:
            entry = self._cache.get((provider, capability, *key))
            if entry is not None and entry[0] > self.clock():
                self._hits[provider] = self._hits.get(provider, 0) + 1
                return entry[1]
            return None

    def invalidate_capabilities(
        self, provider: str, capabilities: tuple[str, ...]
    ) -> None:
        with self._condition:
            self._epoch += 1
            self._cache = {
                key: value
                for key, value in self._cache.items()
                if key[0] != provider or key[1] not in capabilities
            }

    @contextmanager
    def coalesce_route(self, capability: str, key: tuple[Any, ...]) -> Iterator[None]:
        """Serialize identical routing decisions including failed-primary fallback."""
        full = (capability, *key)
        with self._condition:
            while full in self._routes:
                self._condition.wait()
            self._routes.add(full)
        try:
            yield
        finally:
            with self._condition:
                self._routes.discard(full)
                self._condition.notify_all()

    def call(
        self,
        provider: str,
        capability: str,
        key: tuple[Any, ...],
        operation: Callable[[], T],
    ) -> T:
        full = (provider, capability, *key)
        with self._condition:
            while full in self._pending:
                self._condition.wait()
            entry = self._cache.get(full)
            if entry and entry[0] > self.clock():
                self._hits[provider] = self._hits.get(provider, 0) + 1
                return cast(T, entry[1])
            if self._negative.get((provider, capability), 0) > self.clock():
                raise MarketPlanAccessError(
                    "Capability restrita pelo plano (cache 12 h)."
                )
            self._misses[provider] = self._misses.get(provider, 0) + 1
            self._pending.add(full)
            epoch = self._epoch
        try:
            result = operation()
            with self._condition:
                if epoch == self._epoch:
                    self._cache[full] = (
                        self.clock() + TTL[(provider, capability)],
                        result,
                    )
                    while len(self._cache) > 512:
                        self._cache.pop(next(iter(self._cache)))
                self._states[provider, capability] = "available"
            return result
        except MarketDataError as error:
            with self._condition:
                state = "temporarily unavailable"
                if isinstance(error, MarketPlanAccessError):
                    state = "plan restricted"
                    self._negative[provider, capability] = self.clock() + 43200
                elif isinstance(error, MarketRateLimitError):
                    state = "rate limited"
                elif isinstance(error, MarketCredentialsRequiredError):
                    state = "not configured"
                elif isinstance(error, MarketOfflineError):
                    state = "offline"
                self._states[provider, capability] = state
            raise
        finally:
            with self._condition:
                self._pending.discard(full)
                self._condition.notify_all()

    def health(
        self, provider: str, configured: bool, role: str, updates: tuple[str, ...] = ()
    ) -> ProviderHealth:
        with self._condition:
            states = [s for (p, _), s in self._states.items() if p == provider]
            restricted = tuple(
                c
                for (p, c), expiry in self._negative.items()
                if p == provider and expiry > self.clock()
            )
            # A failed capability must not disable the entire provider.
            state = "not configured" if not configured else "available"
            if states and "available" not in states and configured:
                state = (
                    "rate limited"
                    if "rate limited" in states
                    else "temporarily unavailable"
                )
                if all(s == "plan restricted" for s in states):
                    state = "plan restricted"
                if all(s == "offline" for s in states):
                    state = "offline"
            return ProviderHealth(
                provider,
                state,
                role,
                self.usage.count(provider),
                self.usage.budgets[provider],
                restricted,
                self._hits.get(provider, 0),
                self._misses.get(provider, 0),
                self.quota_remaining(provider),
                updates,
            )
