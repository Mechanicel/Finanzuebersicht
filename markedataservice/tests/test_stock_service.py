from __future__ import annotations

import datetime

import pytest

from src.services.base_service import BaseService
from src.services.stock_service import InstrumentNotFoundError, StockService


class FakeMongoRepo:
    def __init__(self, initial=None):
        self.data = dict(initial or {})
        self.writes = 0

    def read(self, isin: str):
        return self.data.get(isin)

    def write(self, isin: str, data):
        self.writes += 1
        self.data[isin] = data


class FakeProvider:
    def __init__(self):
        self.resolve_calls = []
        self.basic_calls = []
        self.price_history_calls = []
        self.symbol_for_isin = {"DE000BASF111": "BAS.DE"}
        self.fund_calls = 0
        self.analyst_calls = 0

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


def _build_service(repo: FakeMongoRepo, provider: FakeProvider) -> StockService:
    service = StockService.__new__(StockService)
    BaseService.__init__(service)
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
    repo = FakeMongoRepo(
        {
            "DE000BASF111": {
                "isin": "DE000BASF111",
                "basic": {"symbol": "BAS.DE", "longName": "BASF SE"},
                "metrics": {},
                "metrics_history": [],
                "price_history": [{"date": "2026-03-20", "close": 10.0}],
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


def test_optional_analyst_block_failure_is_non_fatal():
    repo = FakeMongoRepo()
    provider = FakeProvider()
    service = _build_service(repo, provider)

    payload = service.get_analysis_analysts("DE000BASF111")

    assert provider.analyst_calls == 1
    assert payload["analysts"] == {}
