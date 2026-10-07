from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProviderHealth:
    provider: str
    status: str
    role: str
    requests_today: int
    soft_budget: int
    restricted_capabilities: tuple[str, ...] = ()
    cache_hits: int = 0
    cache_misses: int = 0
    quota_remaining: int | None = None
    cache_updates: tuple[str, ...] = ()

    @property
    def cache_hit_rate(self) -> float:
        total = self.cache_hits + self.cache_misses
        return self.cache_hits / total if total else 0.0
