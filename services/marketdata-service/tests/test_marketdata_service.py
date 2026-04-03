from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SHARED_SRC = ROOT / "shared" / "src"
if str(SHARED_SRC) not in sys.path:
    sys.path.append(str(SHARED_SRC))

SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.append(str(SERVICE_ROOT))

from app.models import CachedInstrumentProfile, InstrumentProfile, UpstreamServiceError
from app.repositories import InMemoryInstrumentProfileCacheRepository
from app.service import MarketDataService


class FakeFMPClient:
    def __init__(self) -> None:
        self.search_calls: list[tuple[str, int]] = []
        self.profile_calls: list[str] = []

    def search_name(self, *, query: str, limit: int):
        self.search_calls.append((query, limit))
        if query == "empty":
            return []
        if query == "broken":
            raise UpstreamServiceError("provider down")
        return [
            {
                "symbol": "CBK.DE",
                "name": "Commerzbank AG",
                "currency": "EUR",
                "exchange": "XETRA",
                "exchangeFullName": "Deutsche Börse Xetra",
            }
        ]

    def profile(self, *, symbol: str):
        self.profile_calls.append(symbol)
        if symbol == "NONE":
            return []
        return [
            {
                "symbol": symbol,
                "companyName": "Commerzbank AG",
                "currency": "EUR",
                "exchange": "XETRA",
                "exchangeFullName": "Deutsche Börse Xetra",
                "price": 18.35,
                "isEtf": False,
                "isFund": False,
            }
        ]


class BrokenRepository:
    def get(self, symbol: str):
        raise RuntimeError("mongo unavailable")

    def upsert(self, symbol: str, payload: dict[str, str], source: str = "fmp_profile_v1"):
        raise RuntimeError("mongo unavailable")


def build_service(*, ttl_seconds: int = 300) -> tuple[MarketDataService, FakeFMPClient, InMemoryInstrumentProfileCacheRepository]:
    client = FakeFMPClient()
    repository = InMemoryInstrumentProfileCacheRepository()
    service = MarketDataService(
        fmp_client=client,
        profile_repository=repository,
        cache_enabled=True,
        profile_cache_ttl_seconds=ttl_seconds,
    )
    return service, client, repository


def test_search_fmp_success_maps_fields() -> None:
    service, client, _ = build_service()

    result = service.search_instruments("Commerzbank", 10)

    assert result.total == 1
    assert result.items[0].symbol == "CBK.DE"
    assert result.items[0].company_name == "Commerzbank AG"
    assert result.items[0].currency == "EUR"
    assert result.items[0].exchange == "XETRA"
    assert result.items[0].exchange_full_name == "Deutsche Börse Xetra"
    assert client.search_calls == [("Commerzbank", 10)]


def test_search_empty_result_list() -> None:
    service, _, _ = build_service()

    result = service.search_instruments("empty", 10)

    assert result.total == 0
    assert result.items == []


def test_search_upstream_error_is_raised() -> None:
    service, _, _ = build_service()

    try:
        service.search_instruments("broken", 10)
        raise AssertionError("Expected UpstreamServiceError")
    except UpstreamServiceError as exc:
        assert "provider down" in exc.message


def test_profile_cache_miss_calls_fmp_and_upserts() -> None:
    service, client, repository = build_service()

    profile = service.get_instrument_profile("cbk.de")

    assert profile.symbol == "CBK.DE"
    assert client.profile_calls == ["CBK.DE"]
    cached = repository.get("CBK.DE")
    assert cached is not None
    assert cached.payload["companyName"] == "Commerzbank AG"


def test_profile_cache_hit_fresh_avoids_fmp_call() -> None:
    service, client, repository = build_service()
    repository._data["CBK.DE"] = CachedInstrumentProfile(
        payload={"symbol": "CBK.DE", "companyName": "Cached Commerzbank", "currency": "EUR"},
        fetched_at=datetime.now(UTC),
    )

    profile = service.get_instrument_profile("cbk.de")

    assert profile.company_name == "Cached Commerzbank"
    assert client.profile_calls == []


def test_profile_cache_stale_refreshes_from_fmp() -> None:
    service, client, repository = build_service(ttl_seconds=60)
    repository._data["CBK.DE"] = CachedInstrumentProfile(
        payload={"symbol": "CBK.DE", "companyName": "Old Commerzbank", "currency": "EUR"},
        fetched_at=datetime.now(UTC) - timedelta(hours=2),
    )

    profile = service.get_instrument_profile("CBK.DE")

    assert profile.company_name == "Commerzbank AG"
    assert client.profile_calls == ["CBK.DE"]
    refreshed = repository.get("CBK.DE")
    assert refreshed is not None
    assert refreshed.payload["companyName"] == "Commerzbank AG"


def test_profile_with_unavailable_repository_falls_back_to_fmp() -> None:
    client = FakeFMPClient()
    service = MarketDataService(
        fmp_client=client,
        profile_repository=BrokenRepository(),
        cache_enabled=True,
        profile_cache_ttl_seconds=300,
    )

    profile = service.get_instrument_profile("CBK.DE")

    assert profile.company_name == "Commerzbank AG"
    assert client.profile_calls == ["CBK.DE"]


def test_instrument_profile_model_validates_full_payload() -> None:
    payload = {
        "symbol": "CBK.DE",
        "price": 18.35,
        "marketCap": 25000000000,
        "beta": 1.05,
        "lastDividend": 0.35,
        "range": "16.0-20.0",
        "change": 0.2,
        "changePercentage": "1.10%",
        "volume": 1234567,
        "averageVolume": 1200000,
        "companyName": "Commerzbank AG",
        "currency": "EUR",
        "cik": "0000000000",
        "isin": "DE000CBK1001",
        "cusip": None,
        "exchangeFullName": "Deutsche Börse Xetra",
        "exchange": "XETRA",
        "industry": "Banks",
        "website": "https://www.commerzbank.de",
        "description": "Banking services",
        "ceo": "Bettina Orlopp",
        "sector": "Financial Services",
        "country": "DE",
        "fullTimeEmployees": "42000",
        "phone": "+49-69-13620",
        "address": "Kaiserplatz",
        "city": "Frankfurt",
        "state": "HE",
        "zip": "60311",
        "image": "https://example.test/logo.png",
        "ipoDate": "1998-01-01",
        "defaultImage": False,
        "isEtf": False,
        "isActivelyTrading": True,
        "isAdr": False,
        "isFund": False,
    }

    profile = InstrumentProfile.model_validate(payload)

    assert profile.symbol == "CBK.DE"
    assert profile.company_name == "Commerzbank AG"
    assert profile.exchange_full_name == "Deutsche Börse Xetra"
    assert profile.is_actively_trading is True
