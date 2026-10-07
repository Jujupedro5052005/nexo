from collections.abc import Callable

from nexo.domain.models.provider_health import ProviderHealth


class GetProviderHealth:
    def __init__(self, snapshot: Callable[[], tuple[ProviderHealth, ...]]) -> None:
        self._snapshot = snapshot

    def execute(self) -> tuple[ProviderHealth, ...]:
        return self._snapshot()
