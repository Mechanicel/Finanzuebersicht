from __future__ import annotations

from app.cache import TTLMemoryCache
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
    InstrumentSearchResponse,
    InstrumentSummary,
    NotFoundError,
    PriceSeriesResponse,
    SeriesPoint,
)
from app.providers import MarketDataProvider


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
    ) -> None:
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
            self._cache_set(self.search_cache, cache_key, items)
        else:
            items = cached
        return InstrumentSearchResponse(query=normalized_query, items=items, total=len(items))

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
