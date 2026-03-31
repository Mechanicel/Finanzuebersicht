from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SHARED_SRC = ROOT / "shared" / "src"
if str(SHARED_SRC) not in sys.path:
    sys.path.append(str(SHARED_SRC))

SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.append(str(SERVICE_ROOT))

import pytest
from fastapi import FastAPI
from finanzuebersicht_shared.models import ApiResponse
from finanzuebersicht_shared.testing import create_test_client

from app.app_factory import _register_marketdata_error_handlers
from app.models import (
    DataInterval,
    DataRange,
    FundamentalsBlock,
    InstrumentDataBlocksResponse,
    InstrumentFullResponse,
    InstrumentSearchItem,
    InstrumentSummary,
    MetricsBlock,
    NotFoundError,
    PricePoint,
    RiskBlock,
    SnapshotBlock,
    UpstreamServiceError,
)
from app.service import MarketDataService


class FakeProvider:
    def __init__(self) -> None:
        self.summary_calls = 0
        self.series_calls = 0
        self.search_calls = 0
        self.last_interval: DataInterval | None = None

    def get_instrument_summary(self, symbol: str) -> InstrumentSummary | None:
        self.summary_calls += 1
        if symbol == "NONE":
            return None
        return InstrumentSummary(symbol=symbol, company_name="Demo Corp", exchange="XETRA", currency="EUR")

    def get_price_series(self, symbol: str, data_range: DataRange, interval: DataInterval) -> list[PricePoint] | None:
        self.series_calls += 1
        self.last_interval = interval
        if symbol == "NONE":
            return None
        if interval == DataInterval.ONE_WEEK:
            return [PricePoint(date=date(2026, 1, 1), close=100.0)]
        return [
            PricePoint(date=date(2026, 1, 1), close=100.0),
            PricePoint(date=date(2026, 1, 2), close=101.0),
        ]

    def get_instrument_blocks(self, symbol: str) -> InstrumentDataBlocksResponse | None:
        if symbol == "NONE":
            return None
        return InstrumentDataBlocksResponse(
            symbol=symbol,
            snapshot=SnapshotBlock(last_price=100.0, change_1d_pct=0.5, volume=1000),
            fundamentals=FundamentalsBlock(),
            metrics=MetricsBlock(),
            risk=RiskBlock(),
        )

    def get_instrument_full(self, symbol: str) -> InstrumentFullResponse | None:
        if symbol == "NONE":
            return None
        return InstrumentFullResponse(
            summary=InstrumentSummary(symbol=symbol, company_name="Demo Corp", exchange="XETRA", currency="EUR"),
            snapshot=SnapshotBlock(last_price=100.0, change_1d_pct=0.5, volume=1000),
            fundamentals=FundamentalsBlock(),
            metrics=MetricsBlock(),
            risk=RiskBlock(),
        )

    def search_instruments(self, query: str, limit: int) -> list[InstrumentSearchItem]:
        self.search_calls += 1
        if query == "empty":
            return []
        return [
            InstrumentSearchItem(
                symbol="DUM",
                company_name="Dummy AG",
                display_name="Dummy",
                exchange="XETRA",
                currency="EUR",
            )
        ][:limit]

    def list_benchmark_options(self):
        return []


def build_service(provider: FakeProvider) -> MarketDataService:
    return MarketDataService(
        provider=provider,
        cache_enabled=True,
        cache_search_ttl_seconds=60,
        cache_summary_ttl_seconds=60,
        cache_price_ttl_seconds=60,
        cache_series_ttl_seconds=60,
        cache_benchmark_ttl_seconds=60,
    )


def test_summary_uses_summary_provider_path() -> None:
    provider = FakeProvider()
    service = build_service(provider)

    summary = service.get_instrument_summary("dum")

    assert summary.symbol == "DUM"
    assert provider.summary_calls == 1
    assert provider.series_calls == 0


def test_price_series_uses_interval_argument() -> None:
    provider = FakeProvider()
    service = build_service(provider)

    payload = service.get_price_series(symbol="DUM", data_range=DataRange.THREE_MONTHS, interval=DataInterval.ONE_WEEK)

    assert payload.interval == DataInterval.ONE_WEEK
    assert len(payload.points) == 1
    assert provider.last_interval == DataInterval.ONE_WEEK


def test_search_empty_result_is_valid_response() -> None:
    provider = FakeProvider()
    service = build_service(provider)

    response = service.search_instruments("empty", limit=10)

    assert response.total == 0
    assert response.items == []


def test_search_cache_hit_avoids_second_provider_call() -> None:
    provider = FakeProvider()
    service = build_service(provider)

    first = service.search_instruments("dummy", limit=10)
    second = service.search_instruments("dummy", limit=10)

    assert first.total == 1
    assert second.total == 1
    assert provider.search_calls == 1


@pytest.mark.parametrize("method", ["get_instrument_summary", "get_instrument_blocks", "get_instrument_full"])
def test_not_found_paths_raise_not_found(method: str) -> None:
    provider = FakeProvider()
    service = build_service(provider)

    with pytest.raises(NotFoundError):
        getattr(service, method)("NONE")


def test_upstream_service_error_is_mapped_to_structured_503() -> None:
    app = FastAPI()
    _register_marketdata_error_handlers(app)

    @app.get("/boom", response_model=ApiResponse[dict])
    async def boom() -> ApiResponse[dict]:
        raise UpstreamServiceError("Temporary provider timeout")

    client = create_test_client(app)
    response = client.get("/boom")

    assert response.status_code == 503
    body = response.json()
    assert body["error"] == "upstream_unavailable"
    assert body["details"][0]["code"] == "upstream_unavailable"
