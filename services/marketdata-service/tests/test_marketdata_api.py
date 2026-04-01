# ruff: noqa: E402
from __future__ import annotations

import sys
from pathlib import Path

import mongomock
import pytest

ROOT = Path(__file__).resolve().parents[3]
SHARED_SRC = ROOT / "shared" / "src"
if str(SHARED_SRC) not in sys.path:
    sys.path.append(str(SHARED_SRC))

SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.append(str(SERVICE_ROOT))

from finanzuebersicht_shared.testing import assert_standard_health_payload, create_test_client

from app.config import get_settings
import app.dependencies as marketdata_dependencies
from app.dependencies import (
    get_hydrated_repository,
    get_marketdata_service,
    get_provider,
    get_selection_cache_repository,
)
from app.main import app


@pytest.fixture(autouse=True)
def reset_singletons(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MARKETDATA_PROVIDER", "inmemory")
    monkeypatch.setattr(marketdata_dependencies, "MongoClient", mongomock.MongoClient)
    get_settings.cache_clear()
    get_marketdata_service.cache_clear()
    get_provider.cache_clear()
    get_selection_cache_repository.cache_clear()
    get_hydrated_repository.cache_clear()


def test_selection_cache_repository_uses_mongo_collection_from_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MONGO_DATABASE", "finanzuebersicht_test")
    monkeypatch.setenv("MARKETDATA_SELECTION_CACHE_COLLECTION", "marketdata_selection_cache_test")

    repository = get_selection_cache_repository()

    assert repository._collection.database.name == "finanzuebersicht_test"
    assert repository._collection.name == "marketdata_selection_cache_test"


def test_health_and_ready() -> None:
    client = create_test_client(app)
    health = client.get("/health")
    ready = client.get("/ready")

    assert health.status_code == 200
    assert_standard_health_payload(health.json(), "marketdata-service")
    assert ready.status_code == 200
    assert_standard_health_payload(ready.json(), "marketdata-service")


def test_instrument_summary_and_prices() -> None:
    client = create_test_client(app)

    summary = client.get("/api/v1/marketdata/instruments/AAPL/summary")
    assert summary.status_code == 200
    assert summary.headers["X-Request-ID"]
    assert summary.headers["X-Correlation-ID"]
    assert summary.json()["data"]["company_name"] == "Apple Inc."

    prices = client.get(
        "/api/v1/marketdata/instruments/AAPL/prices",
        params={"range": "3M", "interval": "1d"},
    )
    assert prices.status_code == 200
    payload = prices.json()["data"]
    assert payload["symbol"] == "AAPL"
    assert payload["range"] == "3M"
    assert len(payload["points"]) == 63
    assert payload["interval"] == "1d"

    weekly = client.get(
        "/api/v1/marketdata/instruments/AAPL/prices",
        params={"range": "3M", "interval": "1wk"},
    )
    assert weekly.status_code == 200
    assert len(weekly.json()["data"]["points"]) < len(payload["points"])


def test_blocks_full_benchmark_and_comparison_endpoints() -> None:
    client = create_test_client(app)

    blocks = client.get("/api/v1/marketdata/instruments/MSFT/blocks")
    assert blocks.status_code == 200
    assert blocks.json()["data"]["snapshot"]["last_price"] > 0

    full = client.get("/api/v1/marketdata/instruments/MSFT/full")
    assert full.status_code == 200
    assert full.json()["data"]["summary"]["symbol"] == "MSFT"

    selection = client.get("/api/v1/marketdata/instruments/MSFT/selection")
    assert selection.status_code == 200
    assert selection.json()["data"]["symbol"] == "MSFT"
    assert selection.json()["data"]["last_price"] > 0

    benchmarks = client.get("/api/v1/marketdata/benchmarks/options")
    assert benchmarks.status_code == 200
    assert benchmarks.json()["data"]["total"] >= 3

    search = client.get("/api/v1/marketdata/benchmarks/search", params={"q": "sp"})
    assert search.status_code == 200
    assert search.json()["data"]["total"] >= 1

    instrument_search = client.get("/api/v1/marketdata/instruments/search", params={"q": "micro", "limit": 5})
    assert instrument_search.status_code == 200
    instrument_payload = instrument_search.json()["data"]
    assert instrument_payload["total"] >= 1
    assert instrument_payload["items"][0]["symbol"] == "MSFT"
    assert "change_1d_pct" in instrument_payload["items"][0]

    comparison = client.post(
        "/api/v1/marketdata/comparisons/series",
        json={
            "symbols": ["AAPL", "MSFT"],
            "benchmark_id": "sp500",
            "range": "1M",
            "interval": "1d",
        },
    )
    assert comparison.status_code == 200
    comparison_data = comparison.json()["data"]
    assert len(comparison_data["series"]) == 3
    assert comparison_data["series"][0]["kind"] == "instrument"
    assert comparison_data["series"][2]["kind"] == "benchmark"


def test_structured_error_responses() -> None:
    client = create_test_client(app)

    missing_instrument = client.get("/api/v1/marketdata/instruments/NONE/summary")
    assert missing_instrument.status_code == 404
    assert missing_instrument.json()["error"] == "not_found"

    missing_benchmark = client.post(
        "/api/v1/marketdata/comparisons/series",
        json={"symbols": ["AAPL"], "benchmark_id": "missing", "range": "1M", "interval": "1d"},
    )
    assert missing_benchmark.status_code == 404
    assert missing_benchmark.json()["error"] == "not_found"

    invalid_query = client.get("/api/v1/marketdata/benchmarks/search", params={"q": "x"})
    assert invalid_query.status_code == 422
    assert invalid_query.json()["error"] == "validation_error"


def test_instrument_search_empty_result() -> None:
    client = create_test_client(app)
    response = client.get("/api/v1/marketdata/instruments/search", params={"q": "does-not-exist"})
    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["total"] == 0
    assert payload["items"] == []


def test_selection_endpoint_triggers_background_hydration_and_persists_full_document() -> None:
    client = create_test_client(app)

    response = client.get("/api/v1/marketdata/instruments/MSFT/selection")

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["symbol"] == "MSFT"

    hydrated_repository = get_hydrated_repository()
    persisted = hydrated_repository._collection.find_one({"symbol": "MSFT"})
    assert persisted is not None
    assert persisted["identity"]["symbol"] == "MSFT"
    assert persisted["snapshot"]["last_price"] > 0


def test_selection_response_stays_ok_if_background_hydration_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = get_provider()

    def _raise_hydration(_symbol: str):
        raise RuntimeError("failed in background")

    monkeypatch.setattr(provider, "get_instrument_hydration_payload", _raise_hydration)
    client = create_test_client(app)

    response = client.get("/api/v1/marketdata/instruments/MSFT/selection")

    assert response.status_code == 200
    assert response.json()["data"]["symbol"] == "MSFT"
