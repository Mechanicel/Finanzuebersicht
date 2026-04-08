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

from app.models import (
    CachedInstrumentProfile,
    InstrumentProfile,
    PersistenceOnlyInstrumentProfile,
    PriceHistoryCacheDocument,
    PriceHistoryRow,
    UpstreamServiceError,
    utcnow,
)
from app.repositories import (
    InMemoryCurrentPriceCacheRepository,
    InMemoryInstrumentProfileCacheRepository,
    InMemoryPriceHistoryCacheRepository,
)
from app.service import MarketDataService


class FakeSeries:
    def __init__(self, values: list[float | None]) -> None:
        self._values = values

    def dropna(self) -> "FakeSeries":
        return FakeSeries([value for value in self._values if value is not None])

    @property
    def empty(self) -> bool:
        return len(self._values) == 0

    @property
    def iloc(self):
        return self

    def __getitem__(self, idx: int):
        return self._values[idx]


class FakeDateIndex:
    def __init__(self, value: date) -> None:
        self._value = value

    def date(self) -> date:
        return self._value


class FakeDataFrame:
    def __init__(self, close_values: list[float | None] | None = None, rows: list[tuple[str, dict]] | None = None) -> None:
        self._close_values = close_values
        self._rows = rows or []

    @property
    def empty(self) -> bool:
        if self._close_values is not None:
            return len(self._close_values) == 0
        return len(self._rows) == 0

    def __getitem__(self, key: str) -> FakeSeries:
        if key != "Close" or self._close_values is None:
            raise KeyError(key)
        return FakeSeries(self._close_values)

    def iterrows(self):
        for date_str, row in self._rows:
            yyyy, mm, dd = [int(part) for part in date_str.split("-")]
            yield FakeDateIndex(date(yyyy, mm, dd)), row


class FakeTicker:
    def __init__(self, symbol: str, calls: list[tuple[str, str, str]]) -> None:
        self._symbol = symbol
        self._calls = calls

    def history(self, period: str, interval: str):
        self._calls.append((self._symbol, period, interval))
        if period == "1d" and interval == "1m":
            return FakeDataFrame(close_values=[31.0, None, 31.48])
        if period == "max" and interval == "1d":
            return FakeDataFrame(
                rows=[
                    ("2026-04-01", {"Open": 30.1, "High": 30.5, "Low": 29.95, "Close": 30.4, "Volume": 1234567}),
                    ("2026-04-03", {"Open": 31.1, "High": 31.6, "Low": 30.9, "Close": 31.48, "Volume": 999999}),
                ]
            )
        if period == "5d" and interval == "1d":
            return FakeDataFrame(
                rows=[
                    ("2026-04-03", {"Open": 31.1, "High": 31.6, "Low": 30.9, "Close": 31.48, "Volume": 999999}),
                    ("2026-04-04", {"Open": 31.5, "High": 32.0, "Low": 31.2, "Close": 31.7, "Volume": 888888}),
                ]
            )
        return FakeDataFrame(close_values=[])


class FakeYFinance:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str]] = []

    def Ticker(self, symbol: str) -> FakeTicker:
        return FakeTicker(symbol, self.calls)


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
        return [{"symbol": "CBK.DE", "name": "Commerzbank AG", "currency": "EUR", "exchange": "XETRA", "exchangeFullName": "Deutsche Börse Xetra"}]

    def profile(self, *, symbol: str):
        self.profile_calls.append(symbol)
        if symbol == "NONE":
            return []
        return [{"symbol": symbol, "companyName": "Commerzbank AG", "currency": "EUR", "exchange": "XETRA", "exchangeFullName": "Deutsche Börse Xetra", "price": 18.35, "isEtf": False, "isFund": False, "marketCap": 25000000000, "cusip": "123456789", "address": "Kaiserplatz", "zip": "60311", "city": "Frankfurt am Main"}]


class BrokenRepository:
    def get(self, symbol: str):
        raise RuntimeError("mongo unavailable")

    def upsert(self, symbol: str, *, visible_profile: dict, persistence_only_profile: dict, source: str = "fmp_profile_v2"):
        raise RuntimeError("mongo unavailable")


def build_service(*, ttl_seconds: int = 300):
    client = FakeFMPClient()
    profile_repository = InMemoryInstrumentProfileCacheRepository()
    current_price_repository = InMemoryCurrentPriceCacheRepository()
    history_repository = InMemoryPriceHistoryCacheRepository()
    service = MarketDataService(
        fmp_client=client,
        profile_repository=profile_repository,
        current_price_repository=current_price_repository,
        price_history_repository=history_repository,
        cache_enabled=True,
        profile_cache_ttl_seconds=ttl_seconds,
    )
    return service, client, profile_repository, current_price_repository, history_repository


def test_search_fmp_success_maps_fields() -> None:
    service, client, _, _, _ = build_service()
    result = service.search_instruments("Commerzbank", 10)
    assert result.total == 1
    assert result.items[0].symbol == "CBK.DE"
    assert client.search_calls == [("Commerzbank", 10)]


def test_profile_cache_miss_calls_fmp_and_upserts_structured_document() -> None:
    service, client, repository, _, _ = build_service()
    profile = service.get_instrument_profile("cbk.de")
    assert profile.symbol == "CBK.DE"
    assert client.profile_calls == ["CBK.DE"]
    assert repository.get("CBK.DE") is not None


def test_profile_cache_hit_fresh_avoids_fmp_call() -> None:
    service, client, repository, _, _ = build_service()
    repository._data["CBK.DE"] = CachedInstrumentProfile(
        symbol="CBK.DE",
        source="fmp_profile_v2",
        visible_profile=InstrumentProfile(symbol="CBK.DE", company_name="Cached Commerzbank", currency="EUR"),
        persistence_only_profile=PersistenceOnlyInstrumentProfile(),
        fetched_at=datetime.now(UTC),
    )
    profile = service.get_instrument_profile("cbk.de")
    assert profile.company_name == "Cached Commerzbank"
    assert client.profile_calls == []


def test_profile_cache_stale_refreshes_from_fmp() -> None:
    service, client, repository, _, _ = build_service(ttl_seconds=60)
    repository._data["CBK.DE"] = CachedInstrumentProfile(
        symbol="CBK.DE",
        source="fmp_profile_v2",
        visible_profile=InstrumentProfile(symbol="CBK.DE", company_name="Old Commerzbank", currency="EUR"),
        persistence_only_profile=PersistenceOnlyInstrumentProfile(),
        fetched_at=datetime.now(UTC) - timedelta(hours=2),
    )
    profile = service.get_instrument_profile("CBK.DE")
    assert profile.company_name == "Commerzbank AG"
    assert client.profile_calls == ["CBK.DE"]


def test_profile_with_unavailable_repository_falls_back_to_fmp() -> None:
    client = FakeFMPClient()
    service = MarketDataService(
        fmp_client=client,
        profile_repository=BrokenRepository(),
        current_price_repository=InMemoryCurrentPriceCacheRepository(),
        price_history_repository=InMemoryPriceHistoryCacheRepository(),
        cache_enabled=True,
        profile_cache_ttl_seconds=300,
    )
    profile = service.get_instrument_profile("CBK.DE")
    assert profile.company_name == "Commerzbank AG"


def test_refresh_price_cache_hit_for_today(monkeypatch) -> None:
    service, _, _, current_price_repository, history_repository = build_service()
    fake_yf = FakeYFinance()
    monkeypatch.setattr(MarketDataService, "_get_yf_module", staticmethod(lambda: fake_yf))

    trade_date = date.today().isoformat()
    current_price_repository.upsert("CBK.DE", trade_date, 31.48)
    history_repository.upsert_document(
        PriceHistoryCacheDocument(
            symbol="CBK.DE",
            interval="1d",
            period_seeded="max",
            history_rows=[PriceHistoryRow(date="2026-04-01", open=30.1, high=30.5, low=29.95, close=30.4, volume=1234567)],
            first_date="2026-04-01",
            last_date="2026-04-01",
            updated_at=utcnow(),
        )
    )

    response = service.refresh_instrument_price("cbk.de")

    assert response.price_source == "cache_today"
    assert response.price_cache_hit is True
    assert response.history_cache_present is True
    assert response.history_action == "enrich_in_background"
    assert fake_yf.calls == []


def test_refresh_price_cache_miss_uses_1d_1m_and_stores(monkeypatch) -> None:
    service, _, _, current_price_repository, _ = build_service()
    fake_yf = FakeYFinance()
    monkeypatch.setattr(MarketDataService, "_get_yf_module", staticmethod(lambda: fake_yf))

    response = service.refresh_instrument_price("cbk.de")

    assert response.price_source == "yfinance_1d_1m"
    assert response.price_cache_hit is False
    assert fake_yf.calls == [("CBK.DE", "1d", "1m")]

    cached = current_price_repository.get("CBK.DE", date.today().isoformat())
    assert cached is not None
    assert cached.current_price == 31.48


def test_period_max_only_for_first_seed(monkeypatch) -> None:
    service, _, _, _, history_repository = build_service()
    fake_yf = FakeYFinance()
    monkeypatch.setattr(MarketDataService, "_get_yf_module", staticmethod(lambda: fake_yf))

    response = service.refresh_instrument_price("CBK.DE")
    assert response.history_action == "seed_max_in_background"

    service.seed_history_max("CBK.DE")

    stored = history_repository.get("CBK.DE")
    assert stored is not None
    assert stored.period_seeded == "max"
    assert ("CBK.DE", "max", "1d") in fake_yf.calls


def test_no_period_max_when_history_exists_and_enrich_uses_5d(monkeypatch) -> None:
    service, _, _, _, history_repository = build_service()
    fake_yf = FakeYFinance()
    monkeypatch.setattr(MarketDataService, "_get_yf_module", staticmethod(lambda: fake_yf))

    history_repository.upsert_document(
        PriceHistoryCacheDocument(
            symbol="CBK.DE",
            interval="1d",
            period_seeded="max",
            history_rows=[PriceHistoryRow(date="2026-04-01", open=30.1, high=30.5, low=29.95, close=30.4, volume=1234567)],
            first_date="2026-04-01",
            last_date="2026-04-01",
            updated_at=utcnow(),
        )
    )

    response = service.refresh_instrument_price("CBK.DE")
    assert response.history_action == "enrich_in_background"

    service.enrich_history_recent("CBK.DE")

    assert ("CBK.DE", "max", "1d") not in fake_yf.calls
    assert ("CBK.DE", "5d", "1d") in fake_yf.calls
    stored = history_repository.get("CBK.DE")
    assert stored is not None
    assert stored.last_date == "2026-04-04"


def test_get_instrument_history_cache_hit_returns_sorted_points() -> None:
    service, _, _, _, history_repository = build_service()
    history_repository.upsert_document(
        PriceHistoryCacheDocument(
            symbol="CBK.DE",
            interval="1d",
            period_seeded="max",
            history_rows=[
                PriceHistoryRow(date="2026-04-03", open=31.1, high=31.6, low=30.9, close=31.48, volume=999999),
                PriceHistoryRow(date="2026-04-01", open=30.1, high=30.5, low=29.95, close=30.4, volume=1234567),
            ],
            first_date="2026-04-01",
            last_date="2026-04-03",
            updated_at=utcnow(),
        )
    )

    response = service.get_instrument_history("cbk.de", "max")

    assert response.symbol == "CBK.DE"
    assert response.cache_present is True
    assert [point.date for point in response.points] == ["2026-04-01", "2026-04-03"]
    assert [point.close for point in response.points] == [30.4, 31.48]


def test_get_instrument_history_cache_miss_seeds_synchronously(monkeypatch) -> None:
    service, _, _, _, history_repository = build_service()
    fake_yf = FakeYFinance()
    monkeypatch.setattr(MarketDataService, "_get_yf_module", staticmethod(lambda: fake_yf))

    response = service.get_instrument_history("cbk.de", "max")

    assert response.cache_present is False
    assert len(response.points) == 2
    assert ("CBK.DE", "max", "1d") in fake_yf.calls
    assert history_repository.get("CBK.DE") is not None


def test_get_instrument_history_range_filtering() -> None:
    service, _, _, _, history_repository = build_service()
    today = date.today()
    within_window = today - timedelta(days=20)
    outside_window = today - timedelta(days=150)
    history_repository.upsert_document(
        PriceHistoryCacheDocument(
            symbol="CBK.DE",
            interval="1d",
            period_seeded="max",
            history_rows=[
                PriceHistoryRow(date=outside_window.isoformat(), open=29.5, high=30.0, low=29.1, close=29.9, volume=111111),
                PriceHistoryRow(date=within_window.isoformat(), open=30.4, high=30.9, low=30.2, close=30.7, volume=222222),
                PriceHistoryRow(date=today.isoformat(), open=31.1, high=31.6, low=30.9, close=31.48, volume=999999),
            ],
            first_date=outside_window.isoformat(),
            last_date=today.isoformat(),
            updated_at=utcnow(),
        )
    )

    response = service.get_instrument_history("CBK.DE", "3m")

    assert [point.date for point in response.points] == [within_window.isoformat(), today.isoformat()]


def test_get_instrument_history_rejects_invalid_range() -> None:
    service, _, _, _, _ = build_service()

    try:
        service.get_instrument_history("CBK.DE", "2m")
        raise AssertionError("expected error")
    except Exception as exc:
        from app.models import BadRequestError

        assert isinstance(exc, BadRequestError)


def test_holdings_summary_returns_partial_warnings(monkeypatch) -> None:
    service, _, _, _, history_repository = build_service()
    fake_yf = FakeYFinance()
    monkeypatch.setattr(MarketDataService, "_get_yf_module", staticmethod(lambda: fake_yf))

    history_repository.upsert_document(
        PriceHistoryCacheDocument(
            symbol="CBK.DE",
            interval="1d",
            period_seeded="max",
            history_rows=[PriceHistoryRow(date="2026-04-01", open=30.1, high=30.5, low=29.95, close=30.4, volume=1234567)],
            first_date="2026-04-01",
            last_date="2026-04-01",
            updated_at=utcnow(),
        )
    )
    result = service.get_holdings_summary("CBK.DE,NONE")
    assert result.total == 2
    assert result.items[0].symbol == "CBK.DE"
    assert result.items[1].coverage == "none"
    assert result.meta["warnings"][0]["symbol"] == "NONE"


def test_financials_rejects_invalid_period() -> None:
    service, _, _, _, _ = build_service()
    try:
        service.get_instrument_financials("CBK.DE", "monthly")
        raise AssertionError("expected BadRequestError")
    except Exception as exc:
        assert "period must be annual or quarterly" in str(exc)
