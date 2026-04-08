# ruff: noqa: E402
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from pymongo.errors import ServerSelectionTimeoutError

ROOT = Path(__file__).resolve().parents[3]
SHARED_SRC = ROOT / "shared" / "src"
if str(SHARED_SRC) not in sys.path:
    sys.path.append(str(SHARED_SRC))

SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.append(str(SERVICE_ROOT))

from finanzuebersicht_shared.testing import assert_standard_health_payload, create_test_client

import app.dependencies as marketdata_dependencies
from app.config import get_settings
from app.dependencies import (
    get_current_price_repository,
    get_fmp_client,
    get_marketdata_service,
    get_price_history_repository,
    get_profile_repository,
)
from app.main import app
from app.models import BadRequestError, UpstreamServiceError
from app.repositories import (
    InMemoryCurrentPriceCacheRepository,
    InMemoryInstrumentProfileCacheRepository,
    InMemoryPriceHistoryCacheRepository,
)


@pytest.fixture(autouse=True)
def reset_singletons(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MARKETDATA_MONGO_ENABLED", "false")
    get_settings.cache_clear()
    get_fmp_client.cache_clear()
    get_profile_repository.cache_clear()
    get_current_price_repository.cache_clear()
    get_price_history_repository.cache_clear()
    get_marketdata_service.cache_clear()


def test_health_and_ready() -> None:
    client = create_test_client(app)
    health = client.get("/health")
    ready = client.get("/ready")

    assert health.status_code == 200
    assert_standard_health_payload(health.json(), "marketdata-service")
    assert ready.status_code == 200
    assert_standard_health_payload(ready.json(), "marketdata-service")


def test_repositories_fallback_to_inmemory_when_mongo_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MARKETDATA_MONGO_ENABLED", "false")
    profile_repository = get_profile_repository()
    current_price_repository = get_current_price_repository()
    history_repository = get_price_history_repository()
    assert isinstance(profile_repository, InMemoryInstrumentProfileCacheRepository)
    assert isinstance(current_price_repository, InMemoryCurrentPriceCacheRepository)
    assert isinstance(history_repository, InMemoryPriceHistoryCacheRepository)


def test_repositories_fallback_to_inmemory_when_mongo_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MARKETDATA_MONGO_ENABLED", "true")

    class BrokenMongoClient:
        def __init__(self, *args, **kwargs) -> None:
            self.admin = self

        def command(self, _command: str):
            raise ServerSelectionTimeoutError("mongo unreachable")

    monkeypatch.setattr(marketdata_dependencies, "MongoClient", BrokenMongoClient)
    get_profile_repository.cache_clear()
    get_current_price_repository.cache_clear()
    get_price_history_repository.cache_clear()

    profile_repository = get_profile_repository()
    current_price_repository = get_current_price_repository()
    history_repository = get_price_history_repository()

    assert isinstance(profile_repository, InMemoryInstrumentProfileCacheRepository)
    assert isinstance(current_price_repository, InMemoryCurrentPriceCacheRepository)
    assert isinstance(history_repository, InMemoryPriceHistoryCacheRepository)


def test_search_endpoint_success(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeFMPClient:
        def search_name(self, *, query: str, limit: int):
            assert query == "Commerzbank"
            assert limit == 10
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
            return []

    monkeypatch.setattr(marketdata_dependencies, "get_fmp_client", lambda: FakeFMPClient())
    get_marketdata_service.cache_clear()

    client = create_test_client(app)
    response = client.get("/api/v1/marketdata/instruments/search", params={"q": "Commerzbank", "limit": 10})

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["total"] == 1
    assert payload["items"][0]["symbol"] == "CBK.DE"
    assert payload["items"][0]["exchange_full_name"] == "Deutsche Börse Xetra"


def test_search_endpoint_empty_results(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeFMPClient:
        def search_name(self, *, query: str, limit: int):
            return []

        def profile(self, *, symbol: str):
            return []

    monkeypatch.setattr(marketdata_dependencies, "get_fmp_client", lambda: FakeFMPClient())
    get_marketdata_service.cache_clear()

    client = create_test_client(app)
    response = client.get("/api/v1/marketdata/instruments/search", params={"q": "NoMatch", "limit": 10})

    assert response.status_code == 200
    assert response.json()["data"]["items"] == []
    assert response.json()["data"]["total"] == 0


def test_search_endpoint_upstream_error_returns_503(monkeypatch: pytest.MonkeyPatch) -> None:
    class BrokenFMPClient:
        def search_name(self, *, query: str, limit: int):
            raise UpstreamServiceError("provider unavailable")

        def profile(self, *, symbol: str):
            return []

    monkeypatch.setattr(marketdata_dependencies, "get_fmp_client", lambda: BrokenFMPClient())
    get_marketdata_service.cache_clear()

    client = create_test_client(app)
    response = client.get("/api/v1/marketdata/instruments/search", params={"q": "Commerzbank", "limit": 10})

    assert response.status_code == 503
    assert response.json()["details"][0]["code"] == "upstream_unavailable"


def test_profile_endpoint_loads_profile(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeFMPClient:
        def search_name(self, *, query: str, limit: int):
            return []

        def profile(self, *, symbol: str):
            assert symbol == "CBK.DE"
            return [{
                "symbol": "CBK.DE",
                "companyName": "Commerzbank AG",
                "currency": "EUR",
                "exchange": "XETRA",
                "marketCap": 25000000000,
                "address": "Kaiserplatz",
                "zip": "60311",
                "city": "Frankfurt am Main",
            }]

    monkeypatch.setattr(marketdata_dependencies, "get_fmp_client", lambda: FakeFMPClient())
    get_marketdata_service.cache_clear()

    client = create_test_client(app)
    response = client.get("/api/v1/marketdata/instruments/CBK.DE/profile")

    assert response.status_code == 200
    assert response.json()["data"]["symbol"] == "CBK.DE"
    payload = response.json()["data"]
    assert payload["company_name"] == "Commerzbank AG"
    assert payload["address_line"] == "Kaiserplatz, 60311 Frankfurt am Main"
    assert "market_cap" not in payload
    assert "payload" not in payload


def test_refresh_price_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeService:
        def __init__(self) -> None:
            self.seed_calls: list[str] = []

        def refresh_instrument_price(self, symbol: str):
            from datetime import UTC, datetime

            from app.models import InstrumentPriceRefreshResponse

            return InstrumentPriceRefreshResponse(
                symbol=symbol.strip().upper(),
                trade_date="2026-04-03",
                current_price=31.48,
                price_source="cache_today",
                price_cache_hit=True,
                history_cache_present=False,
                history_action="seed_max_in_background",
                fetched_at=datetime.now(UTC),
            )

        def seed_history_max(self, symbol: str) -> None:
            self.seed_calls.append(symbol)

        def enrich_history_recent(self, symbol: str) -> None:
            self.seed_calls.append(f"enrich:{symbol}")

    fake_service = FakeService()
    app.dependency_overrides[marketdata_dependencies.get_marketdata_service] = lambda: fake_service
    client = create_test_client(app)
    response = client.post("/api/v1/marketdata/instruments/CBK.DE/refresh-price")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["symbol"] == "CBK.DE"
    assert payload["price_source"] == "cache_today"


def test_history_endpoint_success() -> None:
    from datetime import UTC, datetime

    from app.models import InstrumentHistoryResponse

    class FakeService:
        def get_instrument_history(self, symbol: str, range_value: str):
            assert symbol == "CBK.DE"
            assert range_value == "6m"
            return InstrumentHistoryResponse(
                symbol="CBK.DE",
                range="6m",
                points=[
                    {"date": "2026-04-01", "close": 30.4},
                    {"date": "2026-04-03", "close": 31.48},
                ],
                cache_present=True,
                updated_at=datetime.now(UTC),
            )

    app.dependency_overrides[marketdata_dependencies.get_marketdata_service] = lambda: FakeService()
    client = create_test_client(app)
    response = client.get("/api/v1/marketdata/instruments/CBK.DE/history", params={"range": "6m"})
    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["symbol"] == "CBK.DE"
    assert payload["range"] == "6m"
    assert payload["points"][0]["date"] == "2026-04-01"


def test_history_endpoint_invalid_range_returns_400() -> None:
    class FakeService:
        def get_instrument_history(self, symbol: str, range_value: str):
            raise BadRequestError("range must be one of: 1m, 3m, 6m, ytd, 1y, max")

    app.dependency_overrides[marketdata_dependencies.get_marketdata_service] = lambda: FakeService()
    client = create_test_client(app)
    response = client.get("/api/v1/marketdata/instruments/CBK.DE/history", params={"range": "2m"})
    app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json()["details"][0]["code"] == "bad_request"
