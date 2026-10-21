"""Cooperative operation cancellation, independent of Qt and provider SDKs."""

from contextvars import ContextVar
from threading import Event


class OperationCancelled(RuntimeError):
    pass


current_cancellation: ContextVar[Event | None] = ContextVar(
    "nexo_cancellation", default=None
)


def check_cancelled() -> None:
    token = current_cancellation.get()
    if token is not None and token.is_set():
        raise OperationCancelled("Operação cancelada.")
