from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest
import requests

ROOT = Path(__file__).resolve().parents[3]
SHARED_SRC = ROOT / "shared" / "src"
if str(SHARED_SRC) not in sys.path:
    sys.path.append(str(SHARED_SRC))

SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.append(str(SERVICE_ROOT))

from app.models import DataInterval, DataRange, UpstreamServiceError
from app.providers import YFinanceMarketDataProvider


class FakeTicker:
    def __init__(self, *, info: dict, fast_info: dict, history_map: dict[tuple[str, str], pd.DataFrame]) -> None:
        self.info = info
        self.fast_info = fast_info
        self._history_map = history_map
        self.calls: list[tuple[str, str]] = []

    def history(self, *, period: str, interval: str, timeout: float):
        self.calls.append((period, interval))
        return self._history_map[(period, interval)]


def _history(closes: list[float], *, volumes: list[int] | None = None) -> pd.DataFrame:
    idx = pd.date_range("2026-01-01", periods=len(closes), freq="D")
    payload = {"Close": closes, "Volume": volumes or [1000] * len(closes)}
    return pd.DataFrame(payload, index=idx)


def test_summary_mapping_uses_provider_fields() -> None:
    provider = YFinanceMarketDataProvider(timeout_seconds=3)
    ticker = FakeTicker(
        info={
            "symbol": "AAPL",
            "longName": "Apple Inc.",
            "shortName": "Apple",
            "exchange": "NMS",
            "currency": "USD",
            "isin": "US0378331005",
            "sector": "Technology",
        },
        fast_info={},
        history_map={("1y", "1d"): _history([100, 101])},
    )
    provider._get_ticker = lambda symbol: ticker  # type: ignore[method-assign]

    summary = provider.get_instrument_summary("AAPL")

    assert summary is not None
    assert summary.symbol == "AAPL"
    assert summary.company_name == "Apple Inc."
    assert summary.isin == "US0378331005"


def test_price_series_mapping_uses_range_and_interval_mapping() -> None:
    provider = YFinanceMarketDataProvider(timeout_seconds=3)
    ticker = FakeTicker(
        info={"symbol": "AAPL", "shortName": "Apple", "currency": "USD"},
        fast_info={},
        history_map={("3mo", "1wk"): _history([101, 102, 103])},
    )
    provider._get_ticker = lambda symbol: ticker  # type: ignore[method-assign]

    points = provider.get_price_series("AAPL", DataRange.THREE_MONTHS, DataInterval.ONE_WEEK)

    assert points is not None
    assert len(points) == 3
    assert ticker.calls == [("3mo", "1wk")]




def test_get_ticker_uses_yfinance_without_session(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = YFinanceMarketDataProvider(timeout_seconds=3)
    captured: list[str] = []

    class StableTicker:
        def __init__(self, symbol: str):
            captured.append(symbol)

    monkeypatch.setattr("app.providers.yf.Ticker", StableTicker)

    provider._get_ticker("AAPL")

    assert captured == ["AAPL"]


def test_selection_details_works_with_sessionless_ticker(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = YFinanceMarketDataProvider(timeout_seconds=3)
    history_1y = _history([100, 101], volumes=[1000, 2000])

    class StableTicker:
        def __init__(self, symbol: str):
            self.info = {"symbol": symbol, "shortName": "Apple", "currency": "USD", "exchange": "NMS"}
            self.fast_info = {"lastPrice": 101.0, "previousClose": 100.0, "lastVolume": 2000}

        def history(self, *, period: str, interval: str, timeout: float):
            assert (period, interval) == ("1y", "1d")
            return history_1y

    monkeypatch.setattr("app.providers.yf.Ticker", StableTicker)

    result = provider.get_instrument_selection_details("AAPL")
    summary = provider.get_instrument_summary("AAPL")

    assert result is not None
    assert result.symbol == "AAPL"
    assert result.last_price == 101.0
    assert summary is not None
    assert summary.symbol == "AAPL"

def test_search_ranking_symbol_isin_wkn_company(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = YFinanceMarketDataProvider(timeout_seconds=3)

    class FakeSearch:
        def __init__(self, *, query: str, max_results: int):
            self.quotes = [
                {"symbol": "AAP", "shortname": "Other", "longname": "Other Corp", "isin": "US0000000001"},
                {"symbol": "AAPL", "shortname": "Apple", "longname": "Apple Inc.", "isin": "US0378331005"},
            ]

    monkeypatch.setattr("app.providers.yf.Search", FakeSearch)

    symbol_results = provider.search_instruments("AAPL", limit=5)
    isin_results = provider.search_instruments("US0378331005", limit=5)

    assert symbol_results[0].symbol == "AAPL"
    assert isin_results[0].symbol == "AAPL"


def test_search_by_company_name_and_wkn_best_effort(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = YFinanceMarketDataProvider(timeout_seconds=3)

    class FakeSearch:
        def __init__(self, *, query: str, max_results: int):
            self.quotes = [
                {"symbol": "AAPL", "shortname": "Apple", "longname": "Apple Inc.", "wkn": "865985"},
                {"symbol": "MSFT", "shortname": "Microsoft", "longname": "Microsoft Corp."},
            ]

    monkeypatch.setattr("app.providers.yf.Search", FakeSearch)

    by_name = provider.search_instruments("Apple", limit=5)
    by_wkn = provider.search_instruments("865985", limit=5)

    assert by_name[0].symbol == "AAPL"
    assert by_wkn[0].symbol == "AAPL"
    assert by_wkn[0].wkn == "865985"


def test_search_uses_stable_yfinance_search_signature(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = YFinanceMarketDataProvider(timeout_seconds=3)

    class StableSearch:
        def __init__(self, *, query: str, max_results: int):
            self.quotes = [{"symbol": "AAPL", "shortname": "Apple", "longname": "Apple Inc."}]

    monkeypatch.setattr("app.providers.yf.Search", StableSearch)

    result = provider.search_instruments("AAPL", limit=5)

    assert [item.symbol for item in result] == ["AAPL"]


def test_search_non_upstream_exception_degrades_to_empty(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    provider = YFinanceMarketDataProvider(timeout_seconds=3)

    class BoomSearch:
        def __init__(self, *, query: str, max_results: int):
            raise ValueError("parser issue")

    monkeypatch.setattr("app.providers.yf.Search", BoomSearch)
    caplog.set_level("ERROR")

    result = provider.search_instruments("com", limit=5)

    assert result == []
    assert "marketdata search failed" in caplog.text


def test_search_upstream_error_is_wrapped(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = YFinanceMarketDataProvider(timeout_seconds=3)

    class BoomSearch:
        def __init__(self, *, query: str, max_results: int):
            raise requests.ConnectionError("yahoo down")

    monkeypatch.setattr("app.providers.yf.Search", BoomSearch)

    with pytest.raises(UpstreamServiceError):
        provider.search_instruments("AAPL", limit=5)
