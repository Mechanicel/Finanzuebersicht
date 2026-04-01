from __future__ import annotations

import sys
from pathlib import Path

import mongomock

ROOT = Path(__file__).resolve().parents[3]
SHARED_SRC = ROOT / "shared" / "src"
if str(SHARED_SRC) not in sys.path:
    sys.path.append(str(SHARED_SRC))

SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.append(str(SERVICE_ROOT))

from app.identity import FmpIdentifierResolver
from app.models import InstrumentSelectionDetailsResponse
from app.repositories import (
    InstrumentHydratedRepository,
    InstrumentSelectionCacheRepository,
    SecurityIdentityRepository,
)
from app.service import MarketDataService


class FakeFmpClient:
    def __init__(self, responses: dict[tuple[str, str | None], list[dict[str, object]]], *, should_raise: bool = False) -> None:
        self._responses = responses
        self._should_raise = should_raise
        self.calls: list[tuple[str, str | None, str | None]] = []

    def search_instrument(
        self,
        *,
        symbol: str,
        exchange: str | None = None,
        company_name: str | None = None,
    ) -> list[dict[str, object]]:
        self.calls.append((symbol, exchange, company_name))
        if self._should_raise:
            raise RuntimeError("boom")
        return self._responses.get((symbol, exchange), [])


def test_fmp_resolver_returns_unique_match() -> None:
    client = FakeFmpClient(
        {
            ("CBK", None): [
                {
                    "symbol": "CBK",
                    "exchange": "GER",
                    "companyName": "Commerzbank AG",
                    "isin": "DE000CBK1001",
                    "wkn": "CBK100",
                }
            ]
        }
    )
    resolver = FmpIdentifierResolver(client=client)

    result = resolver.resolve(symbol="CBK.DE", exchange="GER", company_name="Commerzbank AG")

    assert result is not None
    assert result.identity is not None
    assert result.identity.symbol == "CBK.DE"
    assert result.identity.exchange == "GER"
    assert result.identity.isin == "DE000CBK1001"
    assert result.identity.wkn == "CBK100"
    assert result.provider == "fmp"


def test_fmp_resolver_drops_ambiguous_top_matches() -> None:
    client = FakeFmpClient(
        {
            ("MSFT", "XNAS"): [
                {"symbol": "MSFT", "exchange": "XNAS", "companyName": "Microsoft Corporation", "isin": "US1"},
                {"symbol": "MSFT", "exchange": "XNAS", "companyName": "Microsoft Corporation", "isin": "US2"},
            ]
        }
    )
    resolver = FmpIdentifierResolver(client=client)

    result = resolver.resolve(symbol="MSFT", exchange="XNAS", company_name="Microsoft Corporation")

    assert result is None


def test_fmp_resolver_handles_client_error_defensively() -> None:
    client = FakeFmpClient({}, should_raise=True)
    resolver = FmpIdentifierResolver(client=client)

    result = resolver.resolve(symbol="MSFT", exchange="XNAS", company_name="Microsoft Corporation")

    assert result is None


class FakeProvider:
    def get_instrument_selection_details(self, symbol: str) -> InstrumentSelectionDetailsResponse | None:
        return InstrumentSelectionDetailsResponse(
            symbol=symbol,
            isin=None,
            wkn=None,
            company_name="Microsoft Corporation",
            exchange="XNAS",
            currency="USD",
            last_price=100.0,
        )

    def search_instruments(self, query: str, limit: int):
        return []


def test_fmp_resolver_result_is_persisted_in_security_identity_repository() -> None:
    resolver = FmpIdentifierResolver(
        client=FakeFmpClient(
            {
                ("MSFT", "XNAS"): [
                    {
                        "symbol": "MSFT",
                        "exchange": "XNAS",
                        "companyName": "Microsoft Corporation",
                        "isin": "US5949181045",
                        "wkn": "870747",
                    }
                ]
            }
        )
    )
    mongo = mongomock.MongoClient()
    service = MarketDataService(
        provider=FakeProvider(),
        cache_enabled=False,
        cache_search_ttl_seconds=60,
        cache_summary_ttl_seconds=60,
        cache_price_ttl_seconds=60,
        cache_series_ttl_seconds=60,
        cache_benchmark_ttl_seconds=60,
        selection_cache_repository=InstrumentSelectionCacheRepository(mongo["finanzuebersicht"]["selection"]),
        hydrated_repository=InstrumentHydratedRepository(mongo["finanzuebersicht"]["hydrated"]),
        selection_cache_ttl_seconds=60,
        security_identity_repository=SecurityIdentityRepository(mongo["finanzuebersicht"]["identity"]),
        identifier_resolver=resolver,
    )

    selection = service.get_instrument_selection_details("MSFT")

    assert selection.isin == "US5949181045"
    persisted = service.security_identity_repository.get("MSFT", "XNAS")
    assert persisted is not None
    assert persisted.isin == "US5949181045"
    assert persisted.provider == "fmp"
