from __future__ import annotations

from datetime import timedelta

from app.clients.fmp_client import FMPClient
from app.models import BadRequestError, InstrumentProfile, InstrumentSearchItem, InstrumentSearchResponse, NotFoundError, utcnow
from app.repositories import InMemoryInstrumentProfileCacheRepository, InstrumentProfileCacheRepository


class MarketDataService:
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

        cache_key = (cleaned_query.lower(), limit)
        if self._cache_enabled and cache_key in self._search_cache:
            return self._search_cache[cache_key]

        rows = self._fmp_client.search_name(query=cleaned_query, limit=limit)
        items = [
            InstrumentSearchItem.model_validate(
                {
                    "symbol": row.get("symbol", ""),
                    "name": row.get("name") or row.get("companyName") or "",
                    "currency": row.get("currency"),
                    "exchange": row.get("exchange") or row.get("stockExchange"),
                    "exchange_short_name": row.get("exchangeShortName"),
                    "type": row.get("type"),
                }
            )
            for row in rows
            if row.get("symbol") and (row.get("name") or row.get("companyName"))
        ]
        response = InstrumentSearchResponse(query=cleaned_query, items=items, total=len(items))
        if self._cache_enabled:
            self._search_cache[cache_key] = response
        return response

    def get_instrument_profile(self, symbol: str) -> InstrumentProfile:
        normalized = symbol.strip().upper()
        if not normalized:
            raise BadRequestError("symbol must not be empty")

        cached = self._profile_repository.get(normalized)
        if cached is not None and self._is_fresh(cached.fetched_at):
            return cached.profile

        rows = self._fmp_client.profile(symbol=normalized)
        if not rows:
            raise NotFoundError(f"Instrument '{normalized}' not found")

        row = rows[0]
        profile = InstrumentProfile(
            symbol=row.get("symbol") or normalized,
            company_name=row.get("companyName") or normalized,
            currency=row.get("currency"),
            exchange=row.get("exchange") or row.get("stockExchange"),
            exchange_short_name=row.get("exchangeShortName"),
            industry=row.get("industry"),
            sector=row.get("sector"),
            country=row.get("country"),
            description=row.get("description"),
            website=row.get("website"),
            image=row.get("image"),
            market_cap=row.get("mktCap"),
            price=row.get("price"),
            beta=row.get("beta"),
        )

        stored_at = self._profile_repository.upsert(normalized, profile)
        return profile.model_copy(update={"as_of": stored_at})

    def _is_fresh(self, fetched_at) -> bool:
        return utcnow() - fetched_at <= timedelta(seconds=self._profile_cache_ttl_seconds)
