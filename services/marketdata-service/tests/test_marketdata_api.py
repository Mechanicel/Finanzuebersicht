# ruff: noqa: E402
from __future__ import annotations

import sys
from pathlib import Path

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
from app.dependencies import get_marketdata_service, get_provider
from app.main import app


@pytest.fixture(autouse=True)
def reset_singletons(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MARKETDATA_PROVIDER", "inmemory")
    get_settings.cache_clear()
    get_marketdata_service.cache_clear()
    get_provider.cache_clear()


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
