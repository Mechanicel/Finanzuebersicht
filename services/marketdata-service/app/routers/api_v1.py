from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from finanzuebersicht_shared.models import ApiResponse

from app.dependencies import get_marketdata_service
from app.models import (
    BenchmarkOptionsResponse,
    BenchmarkSearchResponse,
    ComparisonSeriesRequest,
    ComparisonSeriesResponse,
    DataInterval,
    DataRange,
    InstrumentDataBlocksResponse,
    InstrumentFullResponse,
    InstrumentSearchResponse,
    InstrumentSelectionDetailsResponse,
    InstrumentSummary,
    PriceSeriesResponse,
)
from app.service import MarketDataService

router = APIRouter(tags=["marketdata"])


@router.get("/marketdata/instruments/{symbol}/summary", response_model=ApiResponse[InstrumentSummary])
async def instrument_summary(
    symbol: str,
    service: MarketDataService = Depends(get_marketdata_service),
) -> ApiResponse[InstrumentSummary]:
    return ApiResponse(data=service.get_instrument_summary(symbol))


@router.get("/marketdata/instruments/search", response_model=ApiResponse[InstrumentSearchResponse])
async def instrument_search(
    q: str = Query(min_length=1),
    limit: int = Query(default=10, ge=1, le=25),
    service: MarketDataService = Depends(get_marketdata_service),
) -> ApiResponse[InstrumentSearchResponse]:
    return ApiResponse(data=service.search_instruments(query=q, limit=limit))


@router.get("/marketdata/instruments/{symbol}/prices", response_model=ApiResponse[PriceSeriesResponse])
async def price_series(
    symbol: str,
    range: DataRange = Query(default=DataRange.ONE_YEAR),
    interval: DataInterval = Query(default=DataInterval.ONE_DAY),
    service: MarketDataService = Depends(get_marketdata_service),
) -> ApiResponse[PriceSeriesResponse]:
    return ApiResponse(data=service.get_price_series(symbol=symbol, data_range=range, interval=interval))


@router.get("/marketdata/instruments/{symbol}/blocks", response_model=ApiResponse[InstrumentDataBlocksResponse])
async def instrument_blocks(
    symbol: str,
    service: MarketDataService = Depends(get_marketdata_service),
) -> ApiResponse[InstrumentDataBlocksResponse]:
    return ApiResponse(data=service.get_instrument_blocks(symbol))



@router.get(
    "/marketdata/instruments/{symbol}/selection",
    response_model=ApiResponse[InstrumentSelectionDetailsResponse],
)
async def instrument_selection_details(
    symbol: str,
    service: MarketDataService = Depends(get_marketdata_service),
) -> ApiResponse[InstrumentSelectionDetailsResponse]:
    return ApiResponse(data=service.get_instrument_selection_details(symbol))


@router.get("/marketdata/instruments/{symbol}/full", response_model=ApiResponse[InstrumentFullResponse])
async def instrument_full(
    symbol: str,
    service: MarketDataService = Depends(get_marketdata_service),
) -> ApiResponse[InstrumentFullResponse]:
    return ApiResponse(data=service.get_instrument_full(symbol))


@router.get("/marketdata/benchmarks/options", response_model=ApiResponse[BenchmarkOptionsResponse])
async def benchmark_options(
    service: MarketDataService = Depends(get_marketdata_service),
) -> ApiResponse[BenchmarkOptionsResponse]:
    return ApiResponse(data=service.list_benchmark_options())


@router.get("/marketdata/benchmarks/search", response_model=ApiResponse[BenchmarkSearchResponse])
async def benchmark_search(
    q: str = Query(min_length=2),
    service: MarketDataService = Depends(get_marketdata_service),
) -> ApiResponse[BenchmarkSearchResponse]:
    return ApiResponse(data=service.search_benchmarks(q))


@router.post("/marketdata/comparisons/series", response_model=ApiResponse[ComparisonSeriesResponse])
async def comparison_series(
    payload: ComparisonSeriesRequest,
    service: MarketDataService = Depends(get_marketdata_service),
) -> ApiResponse[ComparisonSeriesResponse]:
    return ApiResponse(data=service.get_comparison_series(payload))
