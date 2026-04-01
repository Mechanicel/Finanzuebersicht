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
        def __init__(self, *, query: str, max_results: int, timeout: float):
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
        def __init__(self, *, query: str, max_results: int, timeout: float):
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


def test_search_maps_wkn_price_and_change(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = YFinanceMarketDataProvider(timeout_seconds=3)

    class FakeSearch:
        def __init__(self, *, query: str, max_results: int, timeout: float):
            self.quotes = [
                {
                    "symbol": "CBK.DE",
                    "shortname": "Commerzbank",
                    "longname": "Commerzbank AG",
                    "wkn": "CBK100",
                    "regularMarketPrice": 18.35,
                    "regularMarketChangePercent": -1.25,
                }
            ]

    monkeypatch.setattr("app.providers.yf.Search", FakeSearch)

    result = provider.search_instruments("Commerzbank", limit=5)

    assert result[0].symbol == "CBK.DE"
    assert result[0].wkn == "CBK100"
    assert result[0].last_price == 18.35
    assert result[0].change_1d_pct == -1.25


def test_search_prefers_german_equity_over_structured_product_for_company_query(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = YFinanceMarketDataProvider(timeout_seconds=3)

    class FakeSearch:
        def __init__(self, *, query: str, max_results: int, timeout: float):
            self.quotes = [
                {
                    "symbol": "CERT1.DE",
                    "shortname": "Commerzbank Turbo Zertifikat",
                    "longname": "Commerzbank Turbo Zertifikat",
                    "quoteType": "WARRANT",
                    "typeDisp": "Warrant",
                    "exchange": "GER",
                    "isin": "DE000CERT001",
                },
                {
                    "symbol": "CBK.DE",
                    "shortname": "Commerzbank",
                    "longname": "Commerzbank AG",
                    "quoteType": "EQUITY",
                    "typeDisp": "Stock",
                    "exchange": "XETRA",
                    "isin": "DE000CBK1001",
                },
            ]

    monkeypatch.setattr("app.providers.yf.Search", FakeSearch)

    result = provider.search_instruments("Commerzbank", limit=5)

    assert result[0].symbol == "CBK.DE"
    assert result[1].symbol == "CERT1.DE"


def test_search_prefers_german_equity_listing_over_foreign_duplicate_for_german_company_query(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = YFinanceMarketDataProvider(timeout_seconds=3)

    class FakeSearch:
        def __init__(self, *, query: str, max_results: int, timeout: float):
            self.quotes = [
                {
                    "symbol": "VWAGY",
                    "shortname": "Volkswagen ADR",
                    "longname": "Volkswagen AG ADR",
                    "quoteType": "EQUITY",
                    "typeDisp": "Stock",
                    "exchange": "NYSE",
                    "isin": "US9286623034",
                },
                {
                    "symbol": "CERT2.DE",
                    "shortname": "Volkswagen Turbo Zertifikat",
                    "longname": "Volkswagen Turbo Zertifikat",
                    "quoteType": "WARRANT",
                    "typeDisp": "Warrant",
                    "exchange": "GER",
                    "isin": "DE000CERT002",
                },
                {
                    "symbol": "VOW3.DE",
                    "shortname": "Volkswagen Vz",
                    "longname": "Volkswagen AG",
                    "quoteType": "EQUITY",
                    "typeDisp": "Stock",
                    "exchange": "XETRA",
                    "isin": "DE0007664039",
                },
            ]

    monkeypatch.setattr("app.providers.yf.Search", FakeSearch)

    result = provider.search_instruments("Volkswagen", limit=5)

    assert result[0].symbol == "VOW3.DE"
    assert result[1].symbol == "VWAGY"
    assert result[2].symbol == "CERT2.DE"


def test_search_uses_stable_yfinance_search_signature(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = YFinanceMarketDataProvider(timeout_seconds=3)

    class StableSearch:
        def __init__(self, *, query: str, max_results: int, timeout: float):
            self.quotes = [{"symbol": "AAPL", "shortname": "Apple", "longname": "Apple Inc."}]

    monkeypatch.setattr("app.providers.yf.Search", StableSearch)

    result = provider.search_instruments("AAPL", limit=5)

    assert [item.symbol for item in result] == ["AAPL"]


def test_search_non_upstream_exception_degrades_to_empty(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    provider = YFinanceMarketDataProvider(timeout_seconds=3)

    class BoomSearch:
        def __init__(self, *, query: str, max_results: int, timeout: float):
            raise ValueError("parser issue")

    monkeypatch.setattr("app.providers.yf.Search", BoomSearch)
    caplog.set_level("ERROR")

    result = provider.search_instruments("com", limit=5)

    assert result == []
    assert "marketdata search failed" in caplog.text


def test_search_upstream_error_is_wrapped(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = YFinanceMarketDataProvider(timeout_seconds=3)

    class BoomSearch:
        def __init__(self, *, query: str, max_results: int, timeout: float):
            raise requests.ConnectionError("yahoo down")

    monkeypatch.setattr("app.providers.yf.Search", BoomSearch)

    with pytest.raises(UpstreamServiceError):
        provider.search_instruments("AAPL", limit=5)


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
