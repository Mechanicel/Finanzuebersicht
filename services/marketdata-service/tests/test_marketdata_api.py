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
from app.dependencies import get_fmp_client, get_marketdata_service, get_profile_repository
from app.main import app
from app.repositories import InMemoryInstrumentProfileCacheRepository


@pytest.fixture(autouse=True)
def reset_singletons(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MARKETDATA_MONGO_ENABLED", "false")
    get_settings.cache_clear()
    get_fmp_client.cache_clear()
    get_profile_repository.cache_clear()
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
    repository = get_profile_repository()
    assert isinstance(repository, InMemoryInstrumentProfileCacheRepository)


def test_repositories_fallback_to_inmemory_when_mongo_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MARKETDATA_MONGO_ENABLED", "true")

    class BrokenMongoClient:
        def __init__(self, *args, **kwargs) -> None:
            self.admin = self

        def command(self, _command: str):
            raise ServerSelectionTimeoutError("mongo unreachable")

    monkeypatch.setattr(marketdata_dependencies, "MongoClient", BrokenMongoClient)
    get_profile_repository.cache_clear()
    repository = get_profile_repository()
    assert isinstance(repository, InMemoryInstrumentProfileCacheRepository)


def test_search_and_profile_endpoints(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeFMPClient:
        def search_name(self, *, query: str, limit: int):
            assert query == "Apple"
            return [{"symbol": "AAPL", "name": "Apple Inc.", "currency": "USD", "exchange": "NASDAQ"}]

        def profile(self, *, symbol: str):
            assert symbol == "AAPL"
            return [{"symbol": "AAPL", "companyName": "Apple Inc.", "currency": "USD", "exchange": "NASDAQ"}]

    monkeypatch.setattr(marketdata_dependencies, "get_fmp_client", lambda: FakeFMPClient())
    get_marketdata_service.cache_clear()

    client = create_test_client(app)

    search = client.get("/api/v1/marketdata/instruments/search", params={"q": "Apple", "limit": 10})
    assert search.status_code == 200
    assert search.json()["data"]["total"] == 1
    assert search.json()["data"]["items"][0]["symbol"] == "AAPL"

    profile = client.get("/api/v1/marketdata/instruments/AAPL/profile")
    assert profile.status_code == 200
    assert profile.json()["data"]["company_name"] == "Apple Inc."
