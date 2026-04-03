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

from app.models import InstrumentProfile
from app.repositories import InMemoryInstrumentProfileCacheRepository
from app.service import MarketDataService


class FakeFMPClient:
    def __init__(self) -> None:
        self.search_calls = 0
        self.profile_calls = 0

    def search_name(self, *, query: str, limit: int):
        self.search_calls += 1
        if query == "empty":
            return []
        return [
            {
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "exchange": "NASDAQ",
                "exchangeShortName": "NASDAQ",
                "currency": "USD",
                "type": "stock",
            }
        ][:limit]

    def profile(self, *, symbol: str):
        self.profile_calls += 1
        if symbol == "NONE":
            return []
        return [{"symbol": symbol, "companyName": "Apple Inc.", "currency": "USD", "exchange": "NASDAQ"}]


def build_service() -> tuple[MarketDataService, FakeFMPClient, InMemoryInstrumentProfileCacheRepository]:
    client = FakeFMPClient()
    repo = InMemoryInstrumentProfileCacheRepository()
    service = MarketDataService(
        fmp_client=client,
        profile_repository=repo,
        cache_enabled=True,
        profile_cache_ttl_seconds=300,
    )
    return service, client, repo


def test_search_uses_fmp() -> None:
    service, client, _ = build_service()
    payload = service.search_instruments("apple", 10)
    assert payload.total == 1
    assert payload.items[0].symbol == "AAPL"
    assert client.search_calls == 1


def test_search_uses_memory_cache() -> None:
    service, client, _ = build_service()
    service.search_instruments("apple", 10)
    service.search_instruments("apple", 10)
    assert client.search_calls == 1


def test_profile_uses_cached_entry_when_fresh() -> None:
    service, client, repo = build_service()
    repo.upsert("AAPL", InstrumentProfile(symbol="AAPL", company_name="Cached Inc."))
    payload = service.get_instrument_profile("aapl")
    assert payload.company_name == "Cached Inc."
    assert client.profile_calls == 0


def test_profile_fetches_and_persists_when_cache_missing() -> None:
    service, client, repo = build_service()
    payload = service.get_instrument_profile("aapl")
    assert payload.symbol == "AAPL"
    assert client.profile_calls == 1
    assert repo.get("AAPL") is not None


def test_profile_refetches_when_cache_stale() -> None:
    service, client, repo = build_service()
    repo.upsert("AAPL", InstrumentProfile(symbol="AAPL", company_name="Old Inc."))
    repo._data["AAPL"] = repo._data["AAPL"].model_copy(update={"fetched_at": datetime.now(UTC) - timedelta(hours=5)})
    payload = service.get_instrument_profile("AAPL")
    assert payload.company_name == "Apple Inc."
    assert client.profile_calls == 1
