from __future__ import annotations

import datetime

import pytest

from src.services.base_service import BaseService
from src.services.stock_service import InstrumentNotFoundError, StockService


class FakeMongoRepo:
    def __init__(self, initial=None):
        self.data = dict(initial or {})
        self.writes = 0
        self.symbol_data = {}

    def read(self, isin: str):
        return self.data.get(isin)

    def write(self, isin: str, data):
        self.writes += 1
        self.data[isin] = data

    def read_symbol_timeseries(self, symbol: str):
        return self.symbol_data.get(symbol.upper())

    def write_symbol_timeseries(self, symbol: str, payload):
        self.symbol_data[symbol.upper()] = payload


class FakeProvider:
    def __init__(self):
        self.resolve_calls = []
        self.basic_calls = []
        self.price_history_calls = []
        self.symbol_for_isin = {"DE000BASF111": "BAS.DE"}
        self.fund_calls = 0
        self.analyst_calls = 0
        self.benchmark_calls = []

    def resolve_symbol(self, isin: str) -> str:
        self.resolve_calls.append(isin)
        if isin not in self.symbol_for_isin:
            raise LookupError("not found")
        return self.symbol_for_isin[isin]

    def fetch_basic(self, isin: str, symbol: str | None = None):
        self.basic_calls.append((isin, symbol))
        resolved_symbol = symbol or self.resolve_symbol(isin)
        return {"symbol": resolved_symbol, "longName": "BASF SE", "shortName": "BASF"}

    def fetch_price_history(self, isin: str, symbol: str | None = None):
        self.price_history_calls.append((isin, symbol))
        return [
            {"date": "2026-03-20", "close": 49.5},
            {"date": "2026-03-21", "close": 50.0},
            {"date": "2026-03-24", "close": 51.0},
        ]

    def fetch_fund(self, isin: str, symbol: str | None = None):
        self.fund_calls += 1
        raise RuntimeError("No Fund data found")

    def fetch_analysts(self, isin: str, symbol: str | None = None):
        self.analyst_calls += 1
        raise RuntimeError("404 Not Found")

    def fetch_benchmark_timeseries(self, symbol: str):
        self.benchmark_calls.append(symbol)
        return [
            {"date": "2026-03-26", "close": 100.0},
            {"date": "2026-03-27", "close": 101.0},
        ]


def _build_service(repo: FakeMongoRepo, provider: FakeProvider) -> StockService:
    service = StockService.__new__(StockService)
    BaseService.__init__(service)
    service.performance_logging = False
    service.mongo_repo = repo
    service.provider = provider
    return service


def test_get_company_cache_miss_loads_data_and_caches():
    repo = FakeMongoRepo()
    provider = FakeProvider()
    service = _build_service(repo, provider)

    company = service.get_company("DE000BASF111")

    assert company == "BASF SE"
    assert provider.resolve_calls == ["DE000BASF111"]
    assert repo.writes == 1


def test_get_price_uses_cached_history_without_refetch():
    today = datetime.date.today()
    ref_day = today if today.weekday() < 5 else today - datetime.timedelta(days=today.weekday() - 4)
    repo = FakeMongoRepo(
        {
            "DE000BASF111": {
                "isin": "DE000BASF111",
                "basic": {"symbol": "BAS.DE", "longName": "BASF SE"},
                "metrics": {},
                "metrics_history": [],
                "price_history": [{"date": ref_day.isoformat(), "close": 10.0}],
                "etf": {},
            }
        }
    )
    provider = FakeProvider()
    service = _build_service(repo, provider)

    price = service.get_price("DE000BASF111", None)

    assert price == 10.0
    assert provider.price_history_calls == []


def test_get_price_for_non_trading_day_falls_back_to_previous_price():
    repo = FakeMongoRepo()
    provider = FakeProvider()
    service = _build_service(repo, provider)

    weekend_date = datetime.date(2026, 3, 22)
    price = service.get_price("DE000BASF111", weekend_date)

    assert price == 50.0


def test_get_price_raises_for_unknown_isin():
    repo = FakeMongoRepo()
    provider = FakeProvider()
    service = _build_service(repo, provider)

    with pytest.raises(InstrumentNotFoundError):
        service.get_price("INVALIDISIN", None)


def test_symbol_resolution_used_instead_of_raw_isin():
    repo = FakeMongoRepo()
    provider = FakeProvider()
    service = _build_service(repo, provider)

    service.get_price("DE000BASF111", None)

    assert provider.price_history_calls[0][0] == "DE000BASF111"
    assert provider.price_history_calls[0][1] == "BAS.DE"


def test_get_price_does_not_load_optional_fund_or_analyst_blocks():
    repo = FakeMongoRepo()
    provider = FakeProvider()
    service = _build_service(repo, provider)

    service.get_price("DE000BASF111", None)

    assert provider.fund_calls == 0
    assert provider.analyst_calls == 0


def test_benchmark_timeseries_is_cached_after_first_load():
    repo = FakeMongoRepo()
    provider = FakeProvider()
    service = _build_service(repo, provider)

    first = service._get_symbol_timeseries_cached("^GSPC")
    second = service._get_symbol_timeseries_cached("^GSPC")

    assert first["price_history"]
    assert second["price_history"] == first["price_history"]
    assert provider.benchmark_calls == ["^GSPC"]


def test_stale_benchmark_cache_gets_refreshed():
    repo = FakeMongoRepo()
    provider = FakeProvider()
    stale_date = (datetime.date.today() - datetime.timedelta(days=10)).isoformat()
    repo.symbol_data["^GSPC"] = {
        "symbol": "^GSPC",
        "price_history": [{"date": stale_date, "close": 95.0}],
        "as_of": stale_date,
        "source": "yfinance",
    }
    service = _build_service(repo, provider)

    payload = service._get_symbol_timeseries_cached("^GSPC")

    assert provider.benchmark_calls == ["^GSPC"]
    assert payload["as_of"] >= stale_date


def test_optional_analyst_block_failure_is_non_fatal():
    repo = FakeMongoRepo()
    provider = FakeProvider()
    service = _build_service(repo, provider)

    payload = service.get_analysis_analysts("DE000BASF111")

    assert provider.analyst_calls == 1
    assert payload["analysts"] == {}


def test_get_depot_holdings_summary_is_lightweight_and_deduplicated():
    repo = FakeMongoRepo()
    provider = FakeProvider()
    service = _build_service(repo, provider)

    payload = service.get_depot_holdings_summary(["de000basf111", "DE000BASF111", "", "   "])

    assert len(payload["holdings"]) == 1
    assert payload["holdings"][0]["isin"] == "DE000BASF111"
    assert payload["holdings"][0]["symbol"] == "BAS.DE"
    assert payload["holdings"][0]["coverage"] == "depot_summary"
    assert provider.price_history_calls == []


def test_get_depot_holdings_summary_keeps_partial_results_on_single_failure():
    repo = FakeMongoRepo()
    provider = FakeProvider()
    service = _build_service(repo, provider)

    payload = service.get_depot_holdings_summary(["DE000BASF111", "INVALIDISIN"])

    assert len(payload["holdings"]) == 1
    assert payload["holdings"][0]["isin"] == "DE000BASF111"
    assert payload["meta"]["failed"] == 1
    assert payload["meta"]["errors"][0]["isin"] == "INVALIDISIN"
