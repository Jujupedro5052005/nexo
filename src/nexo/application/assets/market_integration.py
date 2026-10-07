from dataclasses import replace

from nexo.domain.interfaces.market_data_provider import (
    MarketAuthenticationError,
    MarketCredentialsRequiredError,
    MarketDataError,
    MarketDataProvider,
    MarketInvalidTokenError,
    MarketPlanAccessError,
    MarketRateLimitError,
)
from nexo.domain.models.asset import Asset
from nexo.domain.models.market_integration import MarketIntegrationStatus


class GetMarketIntegrationStatus:
    def __init__(self, provider: MarketDataProvider) -> None:
        self._provider = provider

    def execute(self) -> MarketIntegrationStatus:
        status = self._provider.get_integration_status()
        return (
            status
            if status is not None
            else MarketIntegrationStatus(
                "brapi",
                False,
                None,
                (),
                "Diagnóstico indisponível para este provider.",
                "unavailable",
            )
        )


class TestMarketConnection:
    """One fresh, small request through the existing uncached provider/client."""

    def __init__(self, provider: MarketDataProvider) -> None:
        self._provider = provider

    def execute(self) -> MarketIntegrationStatus:
        status = GetMarketIntegrationStatus(self._provider).execute()
        try:
            with self._provider.refresh_context(True):
                self._provider.get_quote(Asset("PETR4"))
        except MarketInvalidTokenError:
            return replace(
                status,
                authenticated=False,
                state="invalid_token",
                message="A chave configurada não foi aceita pela brapi.",
            )
        except MarketPlanAccessError:
            return replace(
                status,
                authenticated=True if status.configured else None,
                state="plan_denied",
                message="Este recurso não está disponível no plano atual da brapi.",
            )
        except MarketCredentialsRequiredError:
            return replace(
                status,
                authenticated=None,
                state="credentials_required",
                message=status.public_access_description
                + " "
                + status.configuration_guidance,
            )
        except MarketRateLimitError:
            return replace(
                status,
                authenticated=None,
                state="rate_limited",
                message="O limite de consultas foi atingido. Tente novamente mais tarde.",
            )
        except MarketAuthenticationError:
            return replace(
                status,
                authenticated=None,
                state="authentication_error",
                message="Não foi possível validar o acesso à brapi. Confira a configuração externa.",
            )
        except MarketDataError:
            return replace(
                status,
                authenticated=None,
                state="unavailable",
                message="Não foi possível acessar a brapi. Verifique sua conexão e tente novamente.",
            )
        return replace(
            status,
            authenticated=None,
            state="connected",
            message="Conexão com brapi funcionando. Requisição em modo autenticado. PETR4 é público; este teste não confirma acesso aos ativos protegidos do plano."
            if status.configured
            else "Conexão funcionando em modo sandbox. "
            + status.public_access_description,
        )
