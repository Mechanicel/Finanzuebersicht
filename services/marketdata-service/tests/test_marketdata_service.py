from __future__ import annotations

import sys
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SHARED_SRC = ROOT / "shared" / "src"
if str(SHARED_SRC) not in sys.path:
    sys.path.append(str(SHARED_SRC))

SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.append(str(SERVICE_ROOT))

import pytest
import mongomock
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
    InstrumentSelectionDetailsResponse,
    InstrumentSummary,
    MetricsBlock,
    NotFoundError,
    OPENFIGI_IDENTITY_SOURCE,
    PricePoint,
    RiskBlock,
    SnapshotBlock,
    UpstreamServiceError,
)
from app.repositories import InstrumentSelectionCacheRepository
from app.repositories import InstrumentHydratedRepository
from app.service import MarketDataService


class FakeProvider:
    def __init__(self) -> None:
        self.summary_calls = 0
        self.series_calls = 0
        self.search_calls = 0
        self.selection_calls = 0
        self.last_interval: DataInterval | None = None
        self.selection_response: InstrumentSelectionDetailsResponse | None = None
        self.selection_responses: dict[str, InstrumentSelectionDetailsResponse] = {}
        self.selection_error_symbols: set[str] = set()
        self.search_results: list[InstrumentSearchItem] | None = None
        self.hydration_payload: dict[str, object] | None = None
        self.hydration_calls = 0
        self.raise_on_hydration = False

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

    def get_instrument_selection_details(self, symbol: str) -> InstrumentSelectionDetailsResponse | None:
        self.selection_calls += 1
        if symbol == "NONE":
            return None
        if symbol in self.selection_error_symbols:
            raise RuntimeError("selection failed")
        if symbol in self.selection_responses:
            return self.selection_responses[symbol]
        if self.selection_response is not None:
            return self.selection_response
        return InstrumentSelectionDetailsResponse(
            symbol=symbol,
            isin="US0000000001",
            wkn="ABC123",
            company_name="Demo Corp",
            display_name="Demo",
            exchange="XETRA",
            currency="EUR",
            quote_type="equity",
            asset_type="stock",
            last_price=123.45,
            change_1d_pct=0.7,
            volume=15000,
            as_of=datetime.now(UTC),
        )

    def search_instruments(self, query: str, limit: int) -> list[InstrumentSearchItem]:
        self.search_calls += 1
        if self.search_results is not None:
            return self.search_results[:limit]
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

    def get_instrument_hydration_payload(self, symbol: str) -> dict[str, object] | None:
        self.hydration_calls += 1
        if self.raise_on_hydration:
            raise RuntimeError("hydration failed")
        if self.hydration_payload is not None:
            return self.hydration_payload
        return {
            "identity": {"symbol": symbol},
            "summary": {"symbol": symbol},
            "snapshot": {"last_price": 100.0},
            "fundamentals": {},
            "metrics": {},
            "risk": {},
            "provider_raw": {"provider": "fake"},
        }


def build_service(
    provider: FakeProvider,
    repository: InstrumentSelectionCacheRepository | None = None,
    hydrated_repository: InstrumentHydratedRepository | None = None,
    *,
    cache_enabled: bool = True,
    selection_ttl_seconds: int = 60,
) -> MarketDataService:
    if repository is None:
        client = mongomock.MongoClient()
        repository = InstrumentSelectionCacheRepository(collection=client["finanzuebersicht"]["selection_cache_test"])
    if hydrated_repository is None:
        client = mongomock.MongoClient()
        hydrated_repository = InstrumentHydratedRepository(collection=client["finanzuebersicht"]["hydrated_test"])
    return MarketDataService(
        provider=provider,
        cache_enabled=cache_enabled,
        cache_search_ttl_seconds=60,
        cache_summary_ttl_seconds=60,
        cache_price_ttl_seconds=60,
        cache_series_ttl_seconds=60,
        cache_benchmark_ttl_seconds=60,
        selection_cache_repository=repository,
        hydrated_repository=hydrated_repository,
        selection_cache_ttl_seconds=selection_ttl_seconds,
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
    assert service.search_cache is not None
    assert service.search_cache.get("search:dummy:10") is None
    assert service.search_cache.get("search:openfigi:v1:dummy:10") is not None


def test_search_enriches_top_results_with_missing_fields() -> None:
    provider = FakeProvider()
    provider.search_results = [
        InstrumentSearchItem(
            symbol="CBK.DE",
            company_name="Commerzbank AG",
            display_name="Commerzbank",
            isin=None,
            wkn=None,
            currency="EUR",
            last_price=None,
            change_1d_pct=None,
        ),
        InstrumentSearchItem(
            symbol="AAPL",
            company_name="Apple Inc.",
            display_name="Apple",
            isin="US0378331005",
            wkn="865985",
            currency="USD",
            last_price=171.0,
            change_1d_pct=0.8,
        ),
    ]
    provider.selection_responses["CBK.DE"] = InstrumentSelectionDetailsResponse(
        symbol="CBK.DE",
        isin="DE000CBK1001",
        wkn="CBK100",
        company_name="Commerzbank AG",
        display_name="Commerzbank AG",
        exchange="XETRA",
        currency="EUR",
        quote_type="EQUITY",
        asset_type="stock",
        last_price=18.35,
        change_1d_pct=-1.25,
    )
    service = build_service(provider)

    response = service.search_instruments("commerzbank", limit=10)

    assert response.items[0].symbol == "CBK.DE"
    assert response.items[0].isin == "DE000CBK1001"
    assert response.items[0].wkn == "CBK100"
    assert response.items[0].last_price == 18.35
    assert response.items[0].change_1d_pct == -1.25
    assert response.items[1].isin == "US0378331005"
    assert provider.selection_calls == 1


def test_search_enrichment_errors_keep_raw_item() -> None:
    provider = FakeProvider()
    provider.search_results = [
        InstrumentSearchItem(
            symbol="CBK.DE",
            company_name="Commerzbank AG",
            display_name="Commerzbank",
            currency="EUR",
            last_price=None,
            change_1d_pct=None,
        )
    ]
    provider.selection_error_symbols.add("CBK.DE")
    service = build_service(provider)

    response = service.search_instruments("commerzbank", limit=10)

    assert response.total == 1
    assert response.items[0].symbol == "CBK.DE"
    assert response.items[0].last_price is None
    assert response.items[0].change_1d_pct is None


def test_selection_cache_hit_for_fresh_db_record() -> None:
    provider = FakeProvider()
    client = mongomock.MongoClient()
    collection = client["finanzuebersicht"]["selection_cache_test"]
    repository = InstrumentSelectionCacheRepository(collection=collection)
    fresh = InstrumentSelectionDetailsResponse(
        symbol="DUM",
        isin="US0000000001",
        wkn="ABC123",
        company_name="Demo Cached",
        display_name="Demo Cached",
        exchange="XETRA",
        currency="EUR",
        quote_type="equity",
        asset_type="stock",
        last_price=99.0,
    )
    collection.insert_one(
        {
            "symbol": "DUM",
            "identity_source": OPENFIGI_IDENTITY_SOURCE,
            "payload": fresh.model_dump(mode="json"),
            "fetched_at": datetime.now(UTC) - timedelta(seconds=10),
        }
    )
    service = build_service(provider, repository, cache_enabled=False, selection_ttl_seconds=60)

    response = service.get_instrument_selection_details("dum")

    assert response.company_name == "Demo Cached"
    assert provider.selection_calls == 0


def test_selection_stale_cache_refreshes_provider_and_updates_db() -> None:
    provider = FakeProvider()
    client = mongomock.MongoClient()
    collection = client["finanzuebersicht"]["selection_cache_test"]
    repository = InstrumentSelectionCacheRepository(collection=collection)
    stale = InstrumentSelectionDetailsResponse(
        symbol="DUM",
        company_name="Stale",
        exchange="XETRA",
        currency="EUR",
        last_price=10.0,
    )
    collection.insert_one(
        {
            "symbol": "DUM",
            "identity_source": OPENFIGI_IDENTITY_SOURCE,
            "payload": stale.model_dump(mode="json"),
            "fetched_at": datetime.now(UTC) - timedelta(seconds=120),
        }
    )
    service = build_service(provider, repository, cache_enabled=False, selection_ttl_seconds=30)

    response = service.get_instrument_selection_details("DUM")

    assert response.last_price > 0
    assert provider.selection_calls == 1
    persisted = collection.find_one({"symbol": "DUM"})
    assert persisted is not None
    assert persisted["payload"]["company_name"] == "Demo Corp"
    assert persisted["identity_source"] == OPENFIGI_IDENTITY_SOURCE


def test_selection_cache_miss_loads_from_provider_and_inserts_db() -> None:
    provider = FakeProvider()
    client = mongomock.MongoClient()
    collection = client["finanzuebersicht"]["selection_cache_test"]
    repository = InstrumentSelectionCacheRepository(collection=collection)
    service = build_service(provider, repository, cache_enabled=False, selection_ttl_seconds=60)

    response = service.get_instrument_selection_details("DUM")

    assert response.symbol == "DUM"
    assert provider.selection_calls == 1
    persisted = collection.find_one({"symbol": "DUM"})
    assert persisted is not None
    assert persisted["payload"]["symbol"] == "DUM"
    assert persisted["identity_source"] == OPENFIGI_IDENTITY_SOURCE


def test_selection_merge_keeps_cached_isin_and_wkn_when_refresh_returns_null() -> None:
    provider = FakeProvider()
    provider.selection_response = InstrumentSelectionDetailsResponse(
        symbol="DUM",
        isin=None,
        wkn=None,
        company_name="Fresh Corp",
        display_name="Fresh",
        exchange="XETRA",
        currency="EUR",
        quote_type="equity",
        asset_type="stock",
        last_price=321.0,
    )
    provider.search_results = []
    client = mongomock.MongoClient()
    collection = client["finanzuebersicht"]["selection_cache_test"]
    repository = InstrumentSelectionCacheRepository(collection=collection)
    stale = InstrumentSelectionDetailsResponse(
        symbol="DUM",
        isin="US0000000001",
        wkn="ABC123",
        company_name="Cached Corp",
        display_name="Cached",
        exchange="XETRA",
        currency="EUR",
        quote_type="equity",
        asset_type="stock",
        last_price=100.0,
    )
    collection.insert_one(
        {
            "symbol": "DUM",
            "identity_source": OPENFIGI_IDENTITY_SOURCE,
            "payload": stale.model_dump(mode="json"),
            "fetched_at": datetime.now(UTC) - timedelta(seconds=120),
        }
    )
    service = build_service(provider, repository, cache_enabled=False, selection_ttl_seconds=30)

    response = service.get_instrument_selection_details("DUM")

    assert response.isin == "US0000000001"
    assert response.wkn == "ABC123"
    persisted = collection.find_one({"symbol": "DUM"})
    assert persisted is not None
    assert persisted["payload"]["isin"] == "US0000000001"
    assert persisted["payload"]["wkn"] == "ABC123"


def test_selection_merge_uses_fresh_price_and_keeps_cached_identity_fields() -> None:
    provider = FakeProvider()
    provider.selection_response = InstrumentSelectionDetailsResponse(
        symbol="DUM",
        isin=None,
        wkn=None,
        company_name="",
        display_name="",
        exchange="",
        currency="",
        quote_type=None,
        asset_type=None,
        last_price=250.5,
        change_1d_pct=2.2,
        volume=8888,
    )
    provider.search_results = []
    client = mongomock.MongoClient()
    collection = client["finanzuebersicht"]["selection_cache_test"]
    repository = InstrumentSelectionCacheRepository(collection=collection)
    stale = InstrumentSelectionDetailsResponse(
        symbol="DUM",
        isin="US0000000001",
        wkn="ABC123",
        company_name="Cached Corp",
        display_name="Cached Display",
        exchange="XETRA",
        currency="EUR",
        quote_type="equity",
        asset_type="stock",
        last_price=100.0,
        change_1d_pct=0.1,
        volume=1000,
    )
    collection.insert_one(
        {
            "symbol": "DUM",
            "identity_source": OPENFIGI_IDENTITY_SOURCE,
            "payload": stale.model_dump(mode="json"),
            "fetched_at": datetime.now(UTC) - timedelta(seconds=120),
        }
    )
    service = build_service(provider, repository, cache_enabled=False, selection_ttl_seconds=30)

    response = service.get_instrument_selection_details("DUM")

    assert response.last_price == 250.5
    assert response.change_1d_pct == 2.2
    assert response.volume == 8888
    assert response.company_name == "Cached Corp"
    assert response.display_name == "Cached Display"
    assert response.exchange == "XETRA"
    assert response.currency == "EUR"


def test_selection_merge_ignores_whitespace_identity_updates() -> None:
    provider = FakeProvider()
    provider.selection_response = InstrumentSelectionDetailsResponse(
        symbol="DUM",
        isin="   ",
        wkn="\t",
        company_name="   ",
        display_name="  ",
        exchange=" ",
        currency=" ",
        quote_type=" ",
        asset_type=" ",
        last_price=200.0,
    )
    provider.search_results = []
    client = mongomock.MongoClient()
    collection = client["finanzuebersicht"]["selection_cache_test"]
    repository = InstrumentSelectionCacheRepository(collection=collection)
    stale = InstrumentSelectionDetailsResponse(
        symbol="DUM",
        isin="US0000000001",
        wkn="ABC123",
        company_name="Cached Corp",
        display_name="Cached Display",
        exchange="XETRA",
        currency="EUR",
        quote_type="equity",
        asset_type="stock",
        last_price=100.0,
    )
    collection.insert_one(
        {
            "symbol": "DUM",
            "identity_source": OPENFIGI_IDENTITY_SOURCE,
            "payload": stale.model_dump(mode="json"),
            "fetched_at": datetime.now(UTC) - timedelta(seconds=120),
        }
    )
    service = build_service(provider, repository, cache_enabled=False, selection_ttl_seconds=30)

    response = service.get_instrument_selection_details("DUM")

    assert response.isin == "US0000000001"
    assert response.wkn == "ABC123"
    assert response.company_name == "Cached Corp"
    assert response.display_name == "Cached Display"
    assert response.exchange == "XETRA"
    assert response.currency == "EUR"
    assert response.quote_type == "equity"
    assert response.asset_type == "stock"


def test_selection_cache_without_source_is_ignored() -> None:
    provider = FakeProvider()
    client = mongomock.MongoClient()
    collection = client["finanzuebersicht"]["selection_cache_test"]
    repository = InstrumentSelectionCacheRepository(collection=collection)
    stale = InstrumentSelectionDetailsResponse(
        symbol="DUM",
        company_name="Legacy Cached",
        exchange="XETRA",
        currency="EUR",
        last_price=10.0,
    )
    collection.insert_one(
        {
            "symbol": "DUM",
            "payload": stale.model_dump(mode="json"),
            "fetched_at": datetime.now(UTC) - timedelta(seconds=10),
        }
    )
    service = build_service(provider, repository, cache_enabled=False, selection_ttl_seconds=60)

    response = service.get_instrument_selection_details("DUM")

    assert response.company_name == "Demo Corp"
    assert provider.selection_calls == 1


def test_selection_cache_with_wrong_source_is_ignored() -> None:
    provider = FakeProvider()
    client = mongomock.MongoClient()
    collection = client["finanzuebersicht"]["selection_cache_test"]
    repository = InstrumentSelectionCacheRepository(collection=collection)
    stale = InstrumentSelectionDetailsResponse(
        symbol="DUM",
        company_name="Yahoo Cached",
        exchange="XETRA",
        currency="EUR",
        last_price=10.0,
    )
    collection.insert_one(
        {
            "symbol": "DUM",
            "identity_source": "yahoo_search_v1",
            "payload": stale.model_dump(mode="json"),
            "fetched_at": datetime.now(UTC) - timedelta(seconds=10),
        }
    )
    service = build_service(provider, repository, cache_enabled=False, selection_ttl_seconds=60)

    response = service.get_instrument_selection_details("DUM")

    assert response.company_name == "Demo Corp"
    assert provider.selection_calls == 1


def test_selection_cache_with_openfigi_source_is_used() -> None:
    provider = FakeProvider()
    client = mongomock.MongoClient()
    collection = client["finanzuebersicht"]["selection_cache_test"]
    repository = InstrumentSelectionCacheRepository(collection=collection)
    fresh = InstrumentSelectionDetailsResponse(
        symbol="DUM",
        company_name="OpenFIGI Cached",
        exchange="XETRA",
        currency="EUR",
        last_price=44.0,
    )
    collection.insert_one(
        {
            "symbol": "DUM",
            "identity_source": OPENFIGI_IDENTITY_SOURCE,
            "payload": fresh.model_dump(mode="json"),
            "fetched_at": datetime.now(UTC) - timedelta(seconds=10),
        }
    )
    service = build_service(provider, repository, cache_enabled=False, selection_ttl_seconds=60)

    response = service.get_instrument_selection_details("DUM")

    assert response.company_name == "OpenFIGI Cached"
    assert provider.selection_calls == 0


def test_selection_response_contains_positive_last_price() -> None:
    provider = FakeProvider()
    service = build_service(provider)

    response = service.get_instrument_selection_details("DUM")

    assert response.last_price > 0


def test_selection_enriches_missing_isin_from_search_result() -> None:
    provider = FakeProvider()
    provider.selection_response = InstrumentSelectionDetailsResponse(
        symbol="CBK.DE",
        isin=None,
        wkn="CBK123",
        company_name="Commerzbank AG",
        display_name="Commerzbank",
        exchange="XETRA",
        currency="EUR",
        quote_type="equity",
        asset_type="stock",
        last_price=20.5,
        change_1d_pct=1.3,
        volume=123456,
    )
    provider.search_results = [
        InstrumentSearchItem(
            symbol="CBK.DE",
            company_name="Commerzbank AG",
            display_name="Commerzbank AG",
            isin="DE000CBK1001",
        )
    ]
    service = build_service(provider)

    response = service.get_instrument_selection_details("CBK.DE")

    assert response.isin == "DE000CBK1001"


def test_selection_enriches_missing_wkn_from_search_result() -> None:
    provider = FakeProvider()
    provider.selection_response = InstrumentSelectionDetailsResponse(
        symbol="CBK.DE",
        isin="DE000CBK1001",
        wkn=None,
        company_name="Commerzbank AG",
        display_name="Commerzbank",
        exchange="XETRA",
        currency="EUR",
        quote_type="equity",
        asset_type="stock",
        last_price=20.5,
        change_1d_pct=1.3,
        volume=123456,
    )
    provider.search_results = [
        InstrumentSearchItem(
            symbol="CBK.DE",
            company_name="Commerzbank AG",
            wkn="CBK100",
        )
    ]
    service = build_service(provider)

    response = service.get_instrument_selection_details("CBK.DE")

    assert response.wkn == "CBK100"


def test_selection_keeps_snapshot_price_and_ignores_search_price() -> None:
    provider = FakeProvider()
    provider.selection_response = InstrumentSelectionDetailsResponse(
        symbol="CBK.DE",
        isin=None,
        wkn=None,
        company_name="Commerzbank AG",
        display_name="Commerzbank",
        exchange="XETRA",
        currency="EUR",
        quote_type="equity",
        asset_type="stock",
        last_price=99.9,
        change_1d_pct=2.5,
        volume=777,
    )
    provider.search_results = [
        InstrumentSearchItem(
            symbol="CBK.DE",
            company_name="Commerzbank AG",
            isin="DE000CBK1001",
            wkn="CBK100",
            last_price=10.0,
        )
    ]
    service = build_service(provider)

    response = service.get_instrument_selection_details("CBK.DE")

    assert response.last_price == 99.9
    assert response.change_1d_pct == 2.5
    assert response.volume == 777


@pytest.mark.parametrize(
    "method,argument",
    [
        ("get_instrument_summary", "NONE"),
        ("get_instrument_blocks", "NONE"),
        ("get_instrument_full", "NONE"),
        ("get_instrument_selection_details", "NONE"),
    ],
)
def test_not_found_paths_raise_not_found(method: str, argument: str) -> None:
    provider = FakeProvider()
    service = build_service(provider)

    with pytest.raises(NotFoundError):
        getattr(service, method)(argument)


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


def test_background_hydration_persists_full_document() -> None:
    provider = FakeProvider()
    client = mongomock.MongoClient()
    hydrated_collection = client["finanzuebersicht"]["hydrated_test"]
    hydrated_repository = InstrumentHydratedRepository(collection=hydrated_collection)
    service = build_service(provider, hydrated_repository=hydrated_repository)

    service.hydrate_instrument_in_background("dum")

    persisted = hydrated_collection.find_one({"symbol": "DUM"})
    assert persisted is not None
    assert persisted["identity"]["symbol"] == "DUM"
    assert "hydrated_at" in persisted


def test_background_hydration_errors_do_not_raise() -> None:
    provider = FakeProvider()
    provider.raise_on_hydration = True
    service = build_service(provider)

    service.hydrate_instrument_in_background("dum")

    assert provider.hydration_calls == 1
