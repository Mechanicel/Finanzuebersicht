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
        cache_ttl_seconds: int,
    ) -> None:
        self.provider = provider
        self.cache_enabled = cache_enabled
        self.cache: TTLMemoryCache[object] | None = (
            TTLMemoryCache(ttl_seconds=cache_ttl_seconds) if cache_enabled else None
        )

    def get_instrument_summary(self, symbol: str) -> InstrumentSummary:
        data = self._instrument_data(symbol=symbol, data_range=DataRange.ONE_MONTH)
        return data.summary

    def get_price_series(
        self,
        *,
        symbol: str,
        data_range: DataRange,
        interval: DataInterval,
    ) -> PriceSeriesResponse:
        data = self._instrument_data(symbol=symbol, data_range=data_range)
        return PriceSeriesResponse(
            symbol=data.summary.symbol,
            currency=data.summary.currency,
            range=data_range,
            interval=interval,
            points=data.prices,
        )

    def get_instrument_blocks(self, symbol: str) -> InstrumentDataBlocksResponse:
        data = self._instrument_data(symbol=symbol, data_range=DataRange.ONE_YEAR)
        return InstrumentDataBlocksResponse(
            symbol=data.summary.symbol,
            snapshot=data.snapshot,
            fundamentals=data.fundamentals,
            metrics=data.metrics,
            risk=data.risk,
        )

    def get_instrument_full(self, symbol: str) -> InstrumentFullResponse:
        data = self._instrument_data(symbol=symbol, data_range=DataRange.ONE_YEAR)
        return InstrumentFullResponse(
            summary=data.summary,
            snapshot=data.snapshot,
            fundamentals=data.fundamentals,
            metrics=data.metrics,
            risk=data.risk,
        )

    def list_benchmark_options(self) -> BenchmarkOptionsResponse:
        items = self.provider.list_benchmark_options()
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

    def get_comparison_series(self, payload: ComparisonSeriesRequest) -> ComparisonSeriesResponse:
        series: list[ComparisonSeriesItem] = []

        for symbol in payload.symbols:
            data = self._instrument_data(symbol=symbol, data_range=payload.range)
            series.append(
                ComparisonSeriesItem(
                    series_id=data.summary.symbol,
                    label=data.summary.company_name,
                    kind="instrument",
                    currency=data.summary.currency,
                    points=[SeriesPoint(date=item.date, value=item.close) for item in data.prices],
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

            benchmark_data = self._instrument_data(symbol=benchmark.symbol, data_range=payload.range)
            series.append(
                ComparisonSeriesItem(
                    series_id=benchmark.benchmark_id,
                    label=benchmark.label,
                    kind="benchmark",
                    currency=benchmark_data.summary.currency,
                    points=[SeriesPoint(date=item.date, value=item.close) for item in benchmark_data.prices],
                )
            )

        return ComparisonSeriesResponse(range=payload.range, interval=payload.interval, series=series)

    def _instrument_data(self, *, symbol: str, data_range: DataRange):
        normalized = symbol.strip().upper()
        if not normalized:
            raise BadRequestError("symbol must not be empty")

        cache_key = f"instrument:{normalized}:{data_range}"
        if self.cache_enabled and self.cache is not None:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached

        data = self.provider.get_instrument_data(normalized, data_range)
        if data is None:
            raise NotFoundError(f"Instrument '{normalized}' not found")

        if self.cache_enabled and self.cache is not None:
            self.cache.set(cache_key, data)
        return data
