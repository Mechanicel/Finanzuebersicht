from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

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

def test_openfigi_search_successful_freetext(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = YFinanceMarketDataProvider(timeout_seconds=3)

    monkeypatch.setattr(
        provider._openfigi_client,
        "search",
        lambda *, query, start=0: [
            {
                "ticker": "AAPL",
                "name": "Apple Inc",
                "securityDescription": "Apple Inc. Common Stock",
                "isin": "US0378331005",
                "exchCode": "US",
                "currency": "USD",
                "marketSecDes": "Equity",
                "securityType2": "Common Stock",
                "securityCountry": "US",
                "compositeFIGI": "BBG000B9XRY4",
            }
        ],
    )
    monkeypatch.setattr(provider._openfigi_client, "map", lambda *, payload: [])

    result = provider.search_instruments("Apple", limit=5)

    assert len(result) == 1
    assert result[0].symbol == "AAPL"


def test_openfigi_mapping_to_instrument_search_item(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = YFinanceMarketDataProvider(timeout_seconds=3)
    monkeypatch.setattr(
        provider._openfigi_client,
        "search",
        lambda *, query, start=0: [
            {
                "ticker": "BMW",
                "name": "Bayerische Motoren Werke AG",
                "securityDescription": "BMW AG",
                "isin": "DE0005190003",
                "wkn": "519000",
                "micCode": "XETR",
                "currency": "EUR",
                "marketSecDes": "Equity",
                "securityType2": "Common Stock",
                "securityCountry": "DE",
                "figi": "BBG000BLNNH6",
            }
        ],
    )
    monkeypatch.setattr(provider._openfigi_client, "map", lambda *, payload: [])

    item = provider.search_instruments("BMW", limit=1)[0]

    assert item.symbol == "BMW"
    assert item.company_name == "Bayerische Motoren Werke AG"
    assert item.isin == "DE0005190003"
    assert item.wkn == "519000"
    assert item.exchange == "XETR"
    assert item.currency == "EUR"
    assert item.quote_type == "Equity"
    assert item.asset_type == "Common Stock"
    assert item.country == "DE"
    assert item.last_price is None
    assert item.change_1d_pct is None


def test_openfigi_search_deduplicates_results(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = YFinanceMarketDataProvider(timeout_seconds=3)
    duplicate = {
        "ticker": "AAPL",
        "name": "Apple Inc",
        "isin": "US0378331005",
        "compositeFIGI": "BBG000B9XRY4",
    }
    monkeypatch.setattr(provider._openfigi_client, "search", lambda *, query, start=0: [duplicate, duplicate])
    monkeypatch.setattr(provider._openfigi_client, "map", lambda *, payload: [])

    result = provider.search_instruments("AAPL", limit=5)

    assert len(result) == 1
    assert result[0].symbol == "AAPL"


def test_openfigi_search_upstream_error_is_wrapped(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = YFinanceMarketDataProvider(timeout_seconds=3)

    def _boom(*, query: str, start: int = 0):
        raise UpstreamServiceError()

    monkeypatch.setattr(provider._openfigi_client, "search", _boom)

    with pytest.raises(UpstreamServiceError):
        provider.search_instruments("AAPL", limit=5)


def test_openfigi_search_parser_error_degrades_to_empty(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    provider = YFinanceMarketDataProvider(timeout_seconds=3)
    monkeypatch.setattr(provider._openfigi_client, "search", lambda *, query, start=0: [{"ticker": "AAPL"}])
    monkeypatch.setattr(provider, "_map_openfigi_item", lambda record: 1 / 0)
    caplog.set_level("ERROR")

    result = provider.search_instruments("AAPL", limit=5)

    assert result == []
    assert "marketdata openfigi search parsing failed" in caplog.text


def test_businessinsider_isin_fallback_uses_symbol_aliases() -> None:
    provider = YFinanceMarketDataProvider(timeout_seconds=3)

    class FakeResponse:
        def __init__(self) -> None:
            self.status_code = 200
            self.text = '"CBK|DE000CBK1001|X|Y"'

    class FakeSession:
        def get(self, url: str, timeout: float):
            return FakeResponse()

    provider._session = FakeSession()  # type: ignore[assignment]

    resolved = provider._resolve_isin_via_businessinsider(
        symbol="CBK.DE",
        info={"shortName": "Commerzbank AG", "exchange": "GER"},
    )

    assert resolved == "DE000CBK1001"


def test_safe_isin_uses_mic_aware_symbol_lookup_for_german_suffix_symbols(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = YFinanceMarketDataProvider(timeout_seconds=3)
    calls: list[object] = []

    class PrimaryTicker:
        isin = None

    class LookupTicker:
        def __init__(self, target):
            calls.append(target)
            if target == ("BMW", "XETR"):
                self.isin = "DE0005190003"
            else:
                self.isin = None
            self.info = {}

    monkeypatch.setattr("app.providers.yf.Ticker", LookupTicker)

    resolved = provider._safe_isin(PrimaryTicker(), symbol="BMW.DE", info={"exchange": "GER"})

    assert resolved == "DE0005190003"
    assert calls[0] == ("BMW", "XETR")


def test_symbol_lookup_falls_back_to_plain_ticker_when_tuple_lookup_is_not_supported(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = YFinanceMarketDataProvider(timeout_seconds=3)
    calls: list[object] = []

    class LookupTicker:
        def __init__(self, target):
            calls.append(target)
            if isinstance(target, tuple):
                raise TypeError("tuple lookup unsupported")
            self.isin = None
            self.info = {"isin": "DE0005190003"} if target == "BMW" else {}

    monkeypatch.setattr("app.providers.yf.Ticker", LookupTicker)

    resolved = provider._resolve_isin_via_symbol_lookup(symbol="BMW.DE", info={"exchange": "GER"})

    assert resolved == "DE0005190003"
    assert calls[:2] == [("BMW", "XETR"), "BMW"]


def test_isin_query_candidates_prefer_names_and_include_symbol_aliases() -> None:
    provider = YFinanceMarketDataProvider(timeout_seconds=3)

    candidates = provider._build_isin_query_candidates(
        symbol="CBK.DE",
        info={
            "longName": "Commerzbank AG                I",
            "shortName": "Commerzbank AG",
            "displayName": "Commerzbank",
        },
    )

    assert candidates[0] == "Commerzbank AG I"
    assert "CBK.DE" in candidates
    assert "CBK" in candidates
