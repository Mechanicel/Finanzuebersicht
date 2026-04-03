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
from app.models import UpstreamServiceError
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
            return [{"symbol": "CBK.DE", "companyName": "Commerzbank AG", "currency": "EUR", "exchange": "XETRA"}]

    monkeypatch.setattr(marketdata_dependencies, "get_fmp_client", lambda: FakeFMPClient())
    get_marketdata_service.cache_clear()

    client = create_test_client(app)
    response = client.get("/api/v1/marketdata/instruments/CBK.DE/profile")

    assert response.status_code == 200
    assert response.json()["data"]["symbol"] == "CBK.DE"
    assert response.json()["data"]["company_name"] == "Commerzbank AG"
