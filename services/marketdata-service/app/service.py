from __future__ import annotations

from datetime import date, timedelta
import logging

from app.clients.fmp_client import FMPClient
from app.models import (
    BadRequestError,
    FMPInstrumentProfile,
    InstrumentProfile,
    InstrumentPriceRefreshResponse,
    InstrumentSearchItem,
    InstrumentSearchResponse,
    NotFoundError,
    PriceHistoryCacheDocument,
    PriceHistoryRow,
    PersistenceOnlyInstrumentProfile,
    UpstreamServiceError,
    utcnow,
)
from app.repositories import (
    CurrentPriceCacheRepository,
    InMemoryCurrentPriceCacheRepository,
    InMemoryInstrumentProfileCacheRepository,
    InMemoryPriceHistoryCacheRepository,
    InstrumentProfileCacheRepository,
    PriceHistoryCacheRepository,
)

LOGGER = logging.getLogger(__name__)


class MarketDataService:
    MAX_SEARCH_LIMIT = 20

    def __init__(
        self,
        *,
        fmp_client: FMPClient,
        profile_repository: InstrumentProfileCacheRepository | InMemoryInstrumentProfileCacheRepository,
        current_price_repository: CurrentPriceCacheRepository | InMemoryCurrentPriceCacheRepository,
        price_history_repository: PriceHistoryCacheRepository | InMemoryPriceHistoryCacheRepository,
        cache_enabled: bool,
        profile_cache_ttl_seconds: int,
    ) -> None:
        self._fmp_client = fmp_client
        self._profile_repository = profile_repository
        self._current_price_repository = current_price_repository
        self._price_history_repository = price_history_repository
        self._cache_enabled = cache_enabled
        self._profile_cache_ttl_seconds = profile_cache_ttl_seconds
        self._search_cache: dict[tuple[str, int], InstrumentSearchResponse] = {}

    def search_instruments(self, query: str, limit: int) -> InstrumentSearchResponse:
        cleaned_query = query.strip()
        if len(cleaned_query) < 1:
            raise BadRequestError("query must contain at least 1 character")
        bounded_limit = max(1, min(limit, self.MAX_SEARCH_LIMIT))

        cache_key = (cleaned_query.lower(), bounded_limit)
        if self._cache_enabled and cache_key in self._search_cache:
            return self._search_cache[cache_key]

        rows = self._fmp_client.search_name(query=cleaned_query, limit=bounded_limit)
        items = [
            InstrumentSearchItem.model_validate(
                {
                    "symbol": row.get("symbol", ""),
                    "company_name": row.get("name") or "",
                    "display_name": row.get("name") or "",
                    "currency": row.get("currency"),
                    "exchange": row.get("exchange"),
                    "exchange_full_name": row.get("exchangeFullName"),
                }
            )
            for row in rows
            if row.get("symbol") and row.get("name")
        ]
        response = InstrumentSearchResponse(query=cleaned_query, items=items, total=len(items))
        if self._cache_enabled:
            self._search_cache[cache_key] = response
        return response

    def get_instrument_profile(self, symbol: str) -> InstrumentProfile:
        normalized = symbol.strip().upper()
        if not normalized:
            raise BadRequestError("symbol must not be empty")

        try:
            cached = self._profile_repository.get(normalized)
        except Exception:
            LOGGER.warning("profile cache read failed for symbol '%s'", normalized, exc_info=True)
            cached = None

        if cached is not None and self._is_fresh(cached.fetched_at):
            return cached.visible_profile

        rows = self._fmp_client.profile(symbol=normalized)
        if not rows:
            raise NotFoundError(f"Instrument '{normalized}' not found")

        parsed = FMPInstrumentProfile.model_validate(rows[0] | {"symbol": normalized})
        visible_profile = self._build_visible_profile(parsed)
        persistence_only_profile = self._build_persistence_profile(parsed)

        try:
            self._profile_repository.upsert(
                normalized,
                visible_profile=visible_profile.model_dump(),
                persistence_only_profile=persistence_only_profile.model_dump(),
            )
        except Exception:
            LOGGER.warning("profile cache write failed for symbol '%s'", normalized, exc_info=True)
        return visible_profile

    def refresh_instrument_price(self, symbol: str) -> InstrumentPriceRefreshResponse:
        normalized = symbol.strip().upper()
        if not normalized:
            raise BadRequestError("symbol must not be empty")

        trade_date = date.today().isoformat()

        cached = self._current_price_repository.get(normalized, trade_date)
        if cached is not None:
            current_price = cached.current_price
            price_source = "cache_today"
            price_cache_hit = True
            fetched_at = cached.fetched_at
        else:
            current_price = self._fetch_current_price(normalized)
            stored = self._current_price_repository.upsert(normalized, trade_date, current_price, source="yfinance_1d_1m")
            price_source = "yfinance_1d_1m"
            price_cache_hit = False
            fetched_at = stored.fetched_at

        history_cache_present = self._price_history_repository.get(normalized) is not None
        history_action = "enrich_in_background" if history_cache_present else "seed_max_in_background"

        return InstrumentPriceRefreshResponse(
            symbol=normalized,
            trade_date=trade_date,
            current_price=current_price,
            price_source=price_source,
            price_cache_hit=price_cache_hit,
            history_cache_present=history_cache_present,
            history_action=history_action,
            fetched_at=fetched_at,
        )

    def seed_history_max(self, symbol: str) -> None:
        normalized = symbol.strip().upper()
        try:
            yf = self._get_yf_module()
            ticker = yf.Ticker(normalized)
            data = ticker.history(period="max", interval="1d")
        except Exception as exc:
            raise UpstreamServiceError("Market data provider temporarily unavailable") from exc
        rows = self._to_history_rows(data)
        if not rows:
            raise UpstreamServiceError("Market data provider returned no daily history for seed")

        document = PriceHistoryCacheDocument(
            symbol=normalized,
            interval="1d",
            period_seeded="max",
            history_rows=rows,
            first_date=rows[0].date,
            last_date=rows[-1].date,
            updated_at=utcnow(),
        )
        self._price_history_repository.upsert_document(document)

    def enrich_history_recent(self, symbol: str) -> None:
        normalized = symbol.strip().upper()
        try:
            yf = self._get_yf_module()
            ticker = yf.Ticker(normalized)
            data = ticker.history(period="5d", interval="1d")
        except Exception as exc:
            raise UpstreamServiceError("Market data provider temporarily unavailable") from exc
        rows = self._to_history_rows(data)
        if not rows:
            return
        self._price_history_repository.enrich_history_rows(normalized, rows)

    def _build_visible_profile(self, parsed: FMPInstrumentProfile) -> InstrumentProfile:
        visible_profile = InstrumentProfile.model_validate(parsed.model_dump())
        visible_profile.address_line = self._build_address_line(
            visible_profile.address,
            visible_profile.zip,
            visible_profile.city,
        )
        return visible_profile

    @staticmethod
    def _build_persistence_profile(parsed: FMPInstrumentProfile) -> PersistenceOnlyInstrumentProfile:
        return PersistenceOnlyInstrumentProfile.model_validate(parsed.model_dump())

    @staticmethod
    def _build_address_line(address: str | None, zip_code: str | None, city: str | None) -> str | None:
        prefix_parts = [part.strip() for part in [address] if isinstance(part, str) and part.strip()]
        location_parts = [part.strip() for part in [zip_code, city] if isinstance(part, str) and part.strip()]

        if location_parts:
            prefix_parts.append(" ".join(location_parts))

        if not prefix_parts:
            return None
        return ", ".join(prefix_parts)

    def _is_fresh(self, fetched_at) -> bool:
        return utcnow() - fetched_at <= timedelta(seconds=self._profile_cache_ttl_seconds)

    @staticmethod
    def _get_yf_module():
        try:
            import yfinance as yf
        except ImportError as exc:
            raise UpstreamServiceError("yfinance dependency is unavailable") from exc
        return yf

    def _fetch_current_price(self, symbol: str) -> float:
        try:
            yf = self._get_yf_module()
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1d", interval="1m")
            if getattr(hist, "empty", True):
                raise UpstreamServiceError("Market data provider returned no intraday data")
            close_series = hist["Close"].dropna()
            if getattr(close_series, "empty", True):
                raise UpstreamServiceError("Market data provider returned no close prices")
            last_price = close_series.iloc[-1]
            return float(last_price)
        except UpstreamServiceError:
            raise
        except Exception as exc:
            raise UpstreamServiceError("Market data provider temporarily unavailable") from exc

    @staticmethod
    def _to_history_rows(data) -> list[PriceHistoryRow]:
        if getattr(data, "empty", True):
            return []

        rows: list[PriceHistoryRow] = []
        for index, row in data.iterrows():
            close = row.get("Close")
            open_price = row.get("Open")
            high = row.get("High")
            low = row.get("Low")
            volume = row.get("Volume")
            if any(value is None for value in [close, open_price, high, low, volume]):
                continue
            try:
                rows.append(
                    PriceHistoryRow(
                        date=index.date().isoformat(),
                        open=float(open_price),
                        high=float(high),
                        low=float(low),
                        close=float(close),
                        volume=int(volume),
                    )
                )
            except Exception:
                continue

        rows.sort(key=lambda entry: entry.date)
        return rows
