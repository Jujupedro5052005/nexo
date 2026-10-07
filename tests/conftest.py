import socket

import httpx
import pytest

from nexo.domain.interfaces.portfolio_repository import PortfolioRepository
from nexo.domain.models.portfolio import Portfolio


class InMemoryPortfolioRepository(PortfolioRepository):
    """Test double; unit/UI tests never open the application's database."""

    def __init__(self) -> None:
        self.portfolios: list[Portfolio] = []

    def add(self, portfolio: Portfolio) -> Portfolio:
        if portfolio.id is not None:
            raise ValueError("Expected a new portfolio")
        persisted = Portfolio(name=portfolio.name, id=len(self.portfolios) + 1)
        self.portfolios.append(persisted)
        return persisted

    def list_all(self) -> list[Portfolio]:
        return list(self.portfolios)


@pytest.fixture
def portfolio_repository() -> InMemoryPortfolioRepository:
    return InMemoryPortfolioRepository()


@pytest.fixture(autouse=True)
def forbid_external_network(monkeypatch):
    """Fail even if an adapter swallows a network attempt. MockTransport stays usable."""
    attempts = []

    def blocked(*args, **kwargs):
        attempts.append(True)
        raise AssertionError("Internet real proibida na suíte comum; use fixtures/MockTransport.")

    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket.socket, "connect_ex", blocked)
    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", blocked)
    import requests
    from curl_cffi.requests import Session
    monkeypatch.setattr(requests.Session, "request", blocked)
    monkeypatch.setattr(Session, "request", blocked)
    yield
    if attempts:
        pytest.fail("Tentativa de internet real detectada durante o teste.")
