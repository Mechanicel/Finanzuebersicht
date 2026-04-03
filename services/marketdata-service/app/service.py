from __future__ import annotations

from datetime import timedelta
import logging

from app.clients.fmp_client import FMPClient
from app.models import BadRequestError, InstrumentProfile, InstrumentSearchItem, InstrumentSearchResponse, NotFoundError, utcnow
from app.repositories import InMemoryInstrumentProfileCacheRepository, InstrumentProfileCacheRepository

LOGGER = logging.getLogger(__name__)


class MarketDataService:
    MAX_SEARCH_LIMIT = 20

    def __init__(
        self,
        *,
        fmp_client: FMPClient,
        profile_repository: InstrumentProfileCacheRepository | InMemoryInstrumentProfileCacheRepository,
        cache_enabled: bool,
        profile_cache_ttl_seconds: int,
    ) -> None:
        self._fmp_client = fmp_client
        self._profile_repository = profile_repository
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
            return InstrumentProfile.model_validate(cached.payload | {"symbol": normalized})

        rows = self._fmp_client.profile(symbol=normalized)
        if not rows:
            raise NotFoundError(f"Instrument '{normalized}' not found")

        full_payload = rows[0] | {"symbol": normalized}
        profile = InstrumentProfile.model_validate(full_payload)
        try:
            self._profile_repository.upsert(normalized, full_payload)
        except Exception:
            LOGGER.warning("profile cache write failed for symbol '%s'", normalized, exc_info=True)
        return profile

    def _is_fresh(self, fetched_at) -> bool:
        return utcnow() - fetched_at <= timedelta(seconds=self._profile_cache_ttl_seconds)
