from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MarketIntegrationStatus:
    """Public diagnostic/capabilities; credentials never belong in this model."""

    provider: str
    configured: bool
    authenticated: bool | None
    public_symbols: tuple[str, ...]
    message: str
    state: str = "not_tested"

    @property
    def public_access_description(self) -> str:
        if self.provider == "Yahoo Finance":
            return "Yahoo Finance é a fonte pública principal; cobertura e disponibilidade variam por ativo."
        return (
            f"O Nexo está usando o acesso público da {self.provider}. "
            f"Apenas {', '.join(self.public_symbols)} estão disponíveis sem chave."
        )

    @property
    def configuration_guidance(self) -> str:
        if self.provider == "Yahoo Finance":
            return "Yahoo não exige chave. brapi e bolsai são complementos opcionais configurados externamente."
        return "Configure BRAPI_TOKEN no arquivo .env e reinicie o Nexo para consultar os ativos permitidos pelo seu plano."
