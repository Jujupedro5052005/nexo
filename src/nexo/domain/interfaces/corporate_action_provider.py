from abc import ABC, abstractmethod

from nexo.domain.models.asset import Asset
from nexo.domain.models.official_data import CorporateAction


class CorporateActionProvider(ABC):
    @abstractmethod
    def get_actions(self, asset: Asset) -> tuple[CorporateAction, ...]:
        """External splits; never mutate transactions or reconstructed positions."""
