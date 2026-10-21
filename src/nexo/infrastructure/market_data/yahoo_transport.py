"""Public Yahoo requests run in an owned process, safely abortable on cancellation.

No keys or HTTP sessions cross this boundary. Only our own child is terminated.
Injected adapter fakes do not use this transport.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from multiprocessing import get_context
from time import monotonic
from typing import Any

from nexo.core.cancellation import check_cancelled
from nexo.domain.interfaces.market_data_provider import (
    MarketDataUnavailableError,
    MarketRateLimitError,
)


def _quote_metadata(symbol: str) -> tuple[str, dict[str, Any] | None]:
    """Chart metadata supplies price/currency/time without quoteSummary fundamentals."""
    import yfinance as yf  # type: ignore[import-untyped]

    try:
        ticker = yf.Ticker(symbol)
        ticker.history(
            period="5d",
            interval="1d",
            auto_adjust=False,
            actions=False,
            raise_errors=True,
            timeout=6,
        )
        metadata = ticker.get_history_metadata()
        if not metadata:
            return symbol, None
        keys = (
            "regularMarketPrice",
            "regularMarketTime",
            "currency",
            "longName",
            "shortName",
            "regularMarketDayHigh",
            "regularMarketDayLow",
            "regularMarketVolume",
        )
        data = {key: metadata.get(key) for key in keys}
        # chartPreviousClose can precede the entire requested window; it must not
        # be labelled as yesterday's close or used to invent a daily change.
        return symbol, data
    except Exception:  # noqa: BLE001 -- retain successes from other symbols.
        return symbol, None


def _quote_batch(
    symbols: tuple[str, ...], connection: Any = None
) -> dict[str, dict[str, Any] | None]:
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(_quote_metadata, symbol) for symbol in symbols]
        results = {}
        for future in as_completed(futures):
            symbol, info = future.result()
            results[symbol] = info
            if connection is not None:
                connection.send((None, (symbol, info)))
        return results


def _request(connection: Any, symbol: str, method: str, kwargs: dict[str, Any]) -> None:
    try:
        import yfinance as yf  # type: ignore[import-untyped]

        result = (
            _quote_batch(tuple(kwargs["symbols"]), connection)
            if method == "quotes"
            else (
                yf.Search(symbol, max_results=20).quotes
                if method == "search"
                else getattr(yf.Ticker(symbol), method)(**kwargs)
            )
        )
        connection.send((True, result))
    except Exception as error:  # noqa: BLE001 -- SDK boundary, never forward secret/error payloads.
        connection.send((False, type(error).__name__ == "YFRateLimitError"))
    finally:
        connection.close()


def yahoo_request(symbol: str, method: str, **kwargs: Any) -> Any:
    check_cancelled()
    context = get_context("spawn")
    parent, child = context.Pipe(duplex=False)
    process = context.Process(
        target=_request, args=(child, symbol, method, kwargs), daemon=True
    )
    partial: dict[str, Any] = {}
    try:
        process.start()
        child.close()
        deadline = monotonic() + (16 if method == "quotes" else 25)
        while True:
            check_cancelled()
            if monotonic() >= deadline:
                if method == "quotes" and partial:
                    return partial
                raise MarketDataUnavailableError("Yahoo excedeu o tempo da consulta.")
            if not parent.poll(0.05):
                if not process.is_alive():
                    if method == "quotes" and partial:
                        return partial
                    raise MarketDataUnavailableError(
                        "Processo Yahoo encerrou sem resposta."
                    )
                continue
            check_cancelled()
            ok, payload = parent.recv()
            if ok is None:
                partial[payload[0]] = payload[1]
                continue
            if not ok:
                if payload:
                    raise MarketRateLimitError("Yahoo Finance: limite remoto atingido.")
                raise MarketDataUnavailableError(
                    "Yahoo Finance: consulta indisponível."
                )
            return payload
    except (EOFError, OSError):
        if method == "quotes" and partial:
            return partial
        raise MarketDataUnavailableError(
            "Yahoo Finance: comunicação interrompida."
        ) from None
    finally:
        parent.close()
        child.close()
        if process.pid is not None:
            if process.is_alive():
                process.terminate()
            process.join(timeout=2)
            process.close()
