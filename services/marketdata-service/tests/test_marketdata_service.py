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

from app.models import CachedInstrumentProfile, InstrumentProfile, PersistenceOnlyInstrumentProfile, UpstreamServiceError
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
                "marketCap": 25000000000,
                "cusip": "123456789",
                "address": "Kaiserplatz",
                "zip": "60311",
                "city": "Frankfurt am Main",
            }
        ]


class BrokenRepository:
    def get(self, symbol: str):
        raise RuntimeError("mongo unavailable")

    def upsert(self, symbol: str, *, visible_profile: dict, persistence_only_profile: dict, source: str = "fmp_profile_v2"):
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


def test_profile_cache_miss_calls_fmp_and_upserts_structured_document() -> None:
    service, client, repository = build_service()

    profile = service.get_instrument_profile("cbk.de")

    assert profile.symbol == "CBK.DE"
    assert client.profile_calls == ["CBK.DE"]
    cached = repository.get("CBK.DE")
    assert cached is not None
    assert cached.visible_profile.company_name == "Commerzbank AG"
    assert cached.persistence_only_profile.market_cap == 25000000000
    assert cached.persistence_only_profile.cusip == "123456789"


def test_profile_cache_hit_fresh_avoids_fmp_call() -> None:
    service, client, repository = build_service()
    repository._data["CBK.DE"] = CachedInstrumentProfile(
        symbol="CBK.DE",
        source="fmp_profile_v2",
        visible_profile=InstrumentProfile(
            symbol="CBK.DE",
            company_name="Cached Commerzbank",
            currency="EUR",
            address="Kaiserplatz",
            zip="60311",
            city="Frankfurt",
            address_line="Kaiserplatz, 60311 Frankfurt",
        ),
        persistence_only_profile=PersistenceOnlyInstrumentProfile(),
        fetched_at=datetime.now(UTC),
    )

    profile = service.get_instrument_profile("cbk.de")

    assert profile.company_name == "Cached Commerzbank"
    assert profile.address_line == "Kaiserplatz, 60311 Frankfurt"
    assert client.profile_calls == []


def test_profile_cache_stale_refreshes_from_fmp() -> None:
    service, client, repository = build_service(ttl_seconds=60)
    repository._data["CBK.DE"] = CachedInstrumentProfile(
        symbol="CBK.DE",
        source="fmp_profile_v2",
        visible_profile=InstrumentProfile(symbol="CBK.DE", company_name="Old Commerzbank", currency="EUR"),
        persistence_only_profile=PersistenceOnlyInstrumentProfile(),
        fetched_at=datetime.now(UTC) - timedelta(hours=2),
    )

    profile = service.get_instrument_profile("CBK.DE")

    assert profile.company_name == "Commerzbank AG"
    assert profile.address_line == "Kaiserplatz, 60311 Frankfurt am Main"
    assert client.profile_calls == ["CBK.DE"]


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


def test_instrument_profile_model_validates_curated_payload() -> None:
    payload = {
        "symbol": "CBK.DE",
        "price": 18.35,
        "companyName": "Commerzbank AG",
        "currency": "EUR",
        "isin": "DE000CBK1001",
        "exchangeFullName": "Deutsche Börse Xetra",
        "exchange": "XETRA",
        "industry": "Banks",
        "website": "https://www.commerzbank.de",
        "description": "Banking services",
        "ceo": "Bettina Orlopp",
        "sector": "Financial Services",
        "country": "DE",
        "phone": "+49-69-13620",
        "address": "Kaiserplatz",
        "city": "Frankfurt",
        "zip": "60311",
        "image": "https://example.test/logo.png",
        "address_line": "Kaiserplatz, 60311 Frankfurt",
    }

    profile = InstrumentProfile.model_validate(payload)

    assert profile.symbol == "CBK.DE"
    assert profile.company_name == "Commerzbank AG"
    assert profile.exchange_full_name == "Deutsche Börse Xetra"
    assert profile.address_line == "Kaiserplatz, 60311 Frankfurt"


def test_address_line_builder_ignores_missing_segments() -> None:
    service, _, _ = build_service()

    assert service._build_address_line("Kaiserplatz", "60311", "Frankfurt") == "Kaiserplatz, 60311 Frankfurt"
    assert service._build_address_line("", "60311", "") == "60311"
    assert service._build_address_line(None, None, None) is None
