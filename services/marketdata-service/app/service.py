from __future__ import annotations

import logging
from app.cache import TTLMemoryCache
from datetime import UTC, datetime, timedelta

from app.models import (
    BadRequestError,
    BenchmarkOptionsResponse,
    BenchmarkSearchResponse,
    ComparisonSeriesItem,
    ComparisonSeriesRequest,
    ComparisonSeriesResponse,
    DataInterval,
    DataRange,
    InstrumentDataBlocksResponse,
    InstrumentFullResponse,
    InstrumentSearchItem,
    InstrumentSelectionDetailsResponse,
    InstrumentSearchResponse,
    InstrumentSummary,
    NotFoundError,
    PriceSeriesResponse,
    SeriesPoint,
)
from app.providers import MarketDataProvider
from app.repositories import InstrumentHydratedRepository, InstrumentSelectionCacheRepository


class MarketDataService:
    def __init__(
        self,
        provider: MarketDataProvider,
        *,
        cache_enabled: bool,
        cache_search_ttl_seconds: int,
        cache_summary_ttl_seconds: int,
        cache_price_ttl_seconds: int,
        cache_series_ttl_seconds: int,
        cache_benchmark_ttl_seconds: int,
        selection_cache_repository: InstrumentSelectionCacheRepository,
        hydrated_repository: InstrumentHydratedRepository,
        selection_cache_ttl_seconds: int,
    ) -> None:
        self._logger = logging.getLogger(__name__)
        self.provider = provider
        self.cache_enabled = cache_enabled
        self.summary_cache: TTLMemoryCache[object] | None = (
            TTLMemoryCache(ttl_seconds=cache_summary_ttl_seconds) if cache_enabled else None
        )
        self.price_cache: TTLMemoryCache[object] | None = (
            TTLMemoryCache(ttl_seconds=cache_price_ttl_seconds) if cache_enabled else None
        )
        self.series_cache: TTLMemoryCache[object] | None = (
            TTLMemoryCache(ttl_seconds=cache_series_ttl_seconds) if cache_enabled else None
        )
        self.search_cache: TTLMemoryCache[object] | None = (
            TTLMemoryCache(ttl_seconds=cache_search_ttl_seconds) if cache_enabled else None
        )
        self.benchmark_cache: TTLMemoryCache[object] | None = (
            TTLMemoryCache(ttl_seconds=cache_benchmark_ttl_seconds) if cache_enabled else None
        )
        self.selection_cache_repository = selection_cache_repository
        self.hydrated_repository = hydrated_repository
        self.selection_cache_ttl_seconds = selection_cache_ttl_seconds
        self.selection_memory_cache: TTLMemoryCache[object] | None = (
            TTLMemoryCache(ttl_seconds=selection_cache_ttl_seconds) if cache_enabled else None
        )

    def get_instrument_summary(self, symbol: str) -> InstrumentSummary:
        normalized = self._normalize_symbol(symbol)
        cache_key = f"summary:{normalized}"
        cached = self._cache_get(self.summary_cache, cache_key)
        if cached is not None:
            return cached

        summary = self.provider.get_instrument_summary(normalized)
        if summary is None:
            raise NotFoundError(f"Instrument '{normalized}' not found")
        self._cache_set(self.summary_cache, cache_key, summary)
        return summary

    def get_price_series(
        self,
        *,
        symbol: str,
        data_range: DataRange,
        interval: DataInterval,
    ) -> PriceSeriesResponse:
        normalized = self._normalize_symbol(symbol)
        cache_key = f"prices:{normalized}:{data_range}:{interval}"
        cached = self._cache_get(self.series_cache, cache_key)
        if cached is None:
            points = self.provider.get_price_series(normalized, data_range, interval)
            if points is None:
                raise NotFoundError(f"Instrument '{normalized}' not found")
            self._cache_set(self.series_cache, cache_key, points)
        else:
            points = cached

        summary = self.get_instrument_summary(normalized)
        return PriceSeriesResponse(
            symbol=summary.symbol,
            currency=summary.currency,
            range=data_range,
            interval=interval,
            points=points,
        )

    def get_instrument_blocks(self, symbol: str) -> InstrumentDataBlocksResponse:
        normalized = self._normalize_symbol(symbol)
        cache_key = f"priceblocks:{normalized}"
        cached = self._cache_get(self.price_cache, cache_key)
        if cached is not None:
            return cached
        blocks = self.provider.get_instrument_blocks(normalized)
        if blocks is None:
            raise NotFoundError(f"Instrument '{normalized}' not found")
        self._cache_set(self.price_cache, cache_key, blocks)
        return blocks

    def get_instrument_full(self, symbol: str) -> InstrumentFullResponse:
        normalized = self._normalize_symbol(symbol)
        cache_key = f"full:{normalized}"
        cached = self._cache_get(self.price_cache, cache_key)
        if cached is not None:
            return cached
        full = self.provider.get_instrument_full(normalized)
        if full is None:
            raise NotFoundError(f"Instrument '{normalized}' not found")
        self._cache_set(self.price_cache, cache_key, full)
        return full

    def get_instrument_selection_details(self, symbol: str) -> InstrumentSelectionDetailsResponse:
        normalized = self._normalize_symbol(symbol)
        cache_key = f"selection:{normalized}"

        cached = self._cache_get(self.selection_memory_cache, cache_key)
        if cached is not None:
            return cached

        cached_payload: InstrumentSelectionDetailsResponse | None = None
        db_cached = self.selection_cache_repository.get(normalized)
        if db_cached is not None:
            payload, fetched_at = db_cached
            cached_payload = payload
            if self._is_selection_cache_fresh(fetched_at):
                self._cache_set(self.selection_memory_cache, cache_key, payload)
                return payload

        selection = self.provider.get_instrument_selection_details(normalized)
        if selection is None:
            raise NotFoundError(f"Instrument '{normalized}' not found")
        selection = self._enrich_selection_details(selection)
        if cached_payload is not None:
            selection = self._merge_selection_details(cached_payload, selection)

        persisted_at = self.selection_cache_repository.upsert(normalized, selection)
        if selection.as_of is None:
            selection = selection.model_copy(update={"as_of": persisted_at})
        self._cache_set(self.selection_memory_cache, cache_key, selection)
        return selection

    def hydrate_instrument_in_background(self, symbol: str) -> None:
        normalized = self._normalize_symbol(symbol)
        try:
            payload = self.provider.get_instrument_hydration_payload(normalized)
            if payload is None:
                return
            self.hydrated_repository.upsert(normalized, payload)
        except Exception:
            self._logger.exception("marketdata background hydration failed", extra={"symbol": normalized})

    def _merge_selection_details(
        self,
        cached: InstrumentSelectionDetailsResponse,
        fresh: InstrumentSelectionDetailsResponse,
    ) -> InstrumentSelectionDetailsResponse:
        identity_fields = (
            "isin",
            "wkn",
            "company_name",
            "display_name",
            "exchange",
            "currency",
            "quote_type",
            "asset_type",
        )
        updates: dict[str, str | None] = {}
        for field_name in identity_fields:
            fresh_value = getattr(fresh, field_name)
            if self._is_blank_value(fresh_value):
                updates[field_name] = getattr(cached, field_name)

        if not updates:
            return fresh
        return fresh.model_copy(update=updates)

    def _enrich_selection_details(
        self, selection: InstrumentSelectionDetailsResponse
    ) -> InstrumentSelectionDetailsResponse:
        candidates = self.provider.search_instruments(selection.symbol, limit=10)
        best_match = next((item for item in candidates if item.symbol.upper() == selection.symbol.upper()), None)
        if best_match is None and candidates:
            best_match = candidates[0]
        if best_match is None:
            return selection

        updates: dict[str, str] = {}
        for field_name in ("isin", "wkn", "display_name", "exchange", "quote_type", "asset_type"):
            current_value = getattr(selection, field_name)
            candidate_value = getattr(best_match, field_name)
            if self._is_blank_value(current_value) and not self._is_blank_value(candidate_value):
                updates[field_name] = candidate_value

        if not updates:
            return selection
        return selection.model_copy(update=updates)

    @staticmethod
    def _is_blank_value(value: str | None) -> bool:
        return value is None or value.strip() == ""

    def list_benchmark_options(self) -> BenchmarkOptionsResponse:
        cache_key = "benchmarks:options"
        cached = self._cache_get(self.benchmark_cache, cache_key)
        if cached is None:
            items = self.provider.list_benchmark_options()
            self._cache_set(self.benchmark_cache, cache_key, items)
        else:
            items = cached
        return BenchmarkOptionsResponse(items=items, total=len(items))

    def search_benchmarks(self, query: str) -> BenchmarkSearchResponse:
        normalized = query.strip().lower()
        if len(normalized) < 2:
            raise BadRequestError("query must contain at least 2 characters")

        options = self.provider.list_benchmark_options()
        items = [
            option
            for option in options
            if normalized in option.label.lower()
            or normalized in option.symbol.lower()
            or normalized in option.benchmark_id.lower()
        ]
        return BenchmarkSearchResponse(query=query, items=items, total=len(items))

    def search_instruments(self, query: str, limit: int = 10) -> InstrumentSearchResponse:
        normalized_query = query.strip()
        if not normalized_query:
            raise BadRequestError("query must not be empty")

        bounded_limit = min(max(1, limit), 25)
        normalized_cache_query = normalized_query.lower()
        cache_key = f"search:{normalized_cache_query}:{bounded_limit}"
        cached = self._cache_get(self.search_cache, cache_key)
        if cached is None:
            items = self.provider.search_instruments(normalized_cache_query, bounded_limit)
            items = self._enrich_search_items(items)
            self._cache_set(self.search_cache, cache_key, items)
        else:
            items = cached
        return InstrumentSearchResponse(query=normalized_query, items=items, total=len(items))

    def _enrich_search_items(self, items: list[InstrumentSearchItem]) -> list[InstrumentSearchItem]:
        enriched: list[InstrumentSearchItem] = []
        max_enriched = 5
        enriched_count = 0
        for item in items:
            if enriched_count >= max_enriched or not self._requires_search_enrichment(item):
                enriched.append(item)
                continue
            try:
                details = self.get_instrument_selection_details(item.symbol)
            except Exception:
                enriched.append(item)
                continue
            enriched.append(self._merge_search_item(item, details))
            enriched_count += 1
        return enriched

    @staticmethod
    def _requires_search_enrichment(item: InstrumentSearchItem) -> bool:
        if MarketDataService._is_blank_value(item.isin):
            return True
        if MarketDataService._is_blank_value(item.wkn):
            return True
        if item.last_price is None:
            return True
        return item.change_1d_pct is None

    def _merge_search_item(
        self,
        item: InstrumentSearchItem,
        details: InstrumentSelectionDetailsResponse,
    ) -> InstrumentSearchItem:
        updates: dict[str, object | None] = {}
        for field_name in (
            "isin",
            "wkn",
            "exchange",
            "currency",
            "quote_type",
            "asset_type",
            "last_price",
            "change_1d_pct",
        ):
            item_value = getattr(item, field_name)
            details_value = getattr(details, field_name)
            if item_value is None and details_value is not None:
                updates[field_name] = details_value
            elif (
                isinstance(item_value, str)
                and isinstance(details_value, str)
                and self._is_blank_value(item_value)
                and not self._is_blank_value(details_value)
            ):
                updates[field_name] = details_value

        if self._is_blank_value(item.display_name) and not self._is_blank_value(details.display_name):
            updates["display_name"] = details.display_name
        if self._is_blank_value(item.company_name) and not self._is_blank_value(details.company_name):
            updates["company_name"] = details.company_name

        if not updates:
            return item
        return item.model_copy(update=updates)

    def get_comparison_series(self, payload: ComparisonSeriesRequest) -> ComparisonSeriesResponse:
        series: list[ComparisonSeriesItem] = []

        for symbol in payload.symbols:
            data = self.get_price_series(symbol=symbol, data_range=payload.range, interval=payload.interval)
            series.append(
                ComparisonSeriesItem(
                    series_id=data.symbol,
                    label=self.get_instrument_summary(symbol).company_name,
                    kind="instrument",
                    currency=data.currency,
                    points=[SeriesPoint(date=item.date, value=item.close) for item in data.points],
                )
            )

        if payload.benchmark_id:
            benchmark = next(
                (
                    item
                    for item in self.provider.list_benchmark_options()
                    if item.benchmark_id == payload.benchmark_id
                ),
                None,
            )
            if benchmark is None:
                raise NotFoundError(f"Benchmark '{payload.benchmark_id}' not found")

            benchmark_data = self.get_price_series(
                symbol=benchmark.symbol, data_range=payload.range, interval=payload.interval
            )
            series.append(
                ComparisonSeriesItem(
                    series_id=benchmark.benchmark_id,
                    label=benchmark.label,
                    kind="benchmark",
                    currency=benchmark_data.currency,
                    points=[SeriesPoint(date=item.date, value=item.close) for item in benchmark_data.points],
                )
            )

        return ComparisonSeriesResponse(range=payload.range, interval=payload.interval, series=series)

    def _is_selection_cache_fresh(self, fetched_at: datetime) -> bool:
        if fetched_at.tzinfo is None:
            fetched_at = fetched_at.replace(tzinfo=UTC)
        return datetime.now(UTC) - fetched_at < timedelta(seconds=self.selection_cache_ttl_seconds)

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        normalized = symbol.strip().upper()
        if not normalized:
            raise BadRequestError("symbol must not be empty")
        return normalized

    def _cache_get(self, cache: TTLMemoryCache[object] | None, key: str):
        if self.cache_enabled and cache is not None:
            return cache.get(key)
        return None

    def _cache_set(self, cache: TTLMemoryCache[object] | None, key: str, value: object) -> None:
        if self.cache_enabled and cache is not None:
            cache.set(key, value)
