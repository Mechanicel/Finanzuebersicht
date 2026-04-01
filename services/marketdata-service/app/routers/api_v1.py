from __future__ import annotations

from functools import partial
from typing import Any, Callable, TypeVar

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from finanzuebersicht_shared.models import ApiResponse
from starlette.concurrency import run_in_threadpool

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
T = TypeVar("T")


async def _run_blocking(callable_obj: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    return await run_in_threadpool(partial(callable_obj, *args, **kwargs))


@router.get("/marketdata/instruments/{symbol}/summary", response_model=ApiResponse[InstrumentSummary])
async def instrument_summary(
    symbol: str,
    service: MarketDataService = Depends(get_marketdata_service),
) -> ApiResponse[InstrumentSummary]:
    return ApiResponse(data=await _run_blocking(service.get_instrument_summary, symbol))


@router.get("/marketdata/instruments/search", response_model=ApiResponse[InstrumentSearchResponse])
async def instrument_search(
    q: str = Query(min_length=1),
    limit: int = Query(default=10, ge=1, le=25),
    service: MarketDataService = Depends(get_marketdata_service),
) -> ApiResponse[InstrumentSearchResponse]:
    return ApiResponse(data=await _run_blocking(service.search_instruments, query=q, limit=limit))


@router.get("/marketdata/instruments/{symbol}/prices", response_model=ApiResponse[PriceSeriesResponse])
async def price_series(
    symbol: str,
    range: DataRange = Query(default=DataRange.ONE_YEAR),
    interval: DataInterval = Query(default=DataInterval.ONE_DAY),
    service: MarketDataService = Depends(get_marketdata_service),
) -> ApiResponse[PriceSeriesResponse]:
    return ApiResponse(
        data=await _run_blocking(service.get_price_series, symbol=symbol, data_range=range, interval=interval)
    )


@router.get("/marketdata/instruments/{symbol}/blocks", response_model=ApiResponse[InstrumentDataBlocksResponse])
async def instrument_blocks(
    symbol: str,
    service: MarketDataService = Depends(get_marketdata_service),
) -> ApiResponse[InstrumentDataBlocksResponse]:
    return ApiResponse(data=await _run_blocking(service.get_instrument_blocks, symbol))



@router.get(
    "/marketdata/instruments/{symbol}/selection",
    response_model=ApiResponse[InstrumentSelectionDetailsResponse],
)
async def instrument_selection_details(
    symbol: str,
    background_tasks: BackgroundTasks,
    service: MarketDataService = Depends(get_marketdata_service),
) -> ApiResponse[InstrumentSelectionDetailsResponse]:
    payload = await _run_blocking(service.get_instrument_selection_details, symbol)
    should_hydrate = await _run_blocking(service.should_trigger_background_hydration, symbol)
    if should_hydrate:
        background_tasks.add_task(service.hydrate_instrument_in_background, symbol)
    return ApiResponse(data=payload)


@router.get("/marketdata/instruments/{symbol}/full", response_model=ApiResponse[InstrumentFullResponse])
async def instrument_full(
    symbol: str,
    service: MarketDataService = Depends(get_marketdata_service),
) -> ApiResponse[InstrumentFullResponse]:
    return ApiResponse(data=await _run_blocking(service.get_instrument_full, symbol))


@router.get("/marketdata/benchmarks/options", response_model=ApiResponse[BenchmarkOptionsResponse])
async def benchmark_options(
    service: MarketDataService = Depends(get_marketdata_service),
) -> ApiResponse[BenchmarkOptionsResponse]:
    return ApiResponse(data=await _run_blocking(service.list_benchmark_options))


@router.get("/marketdata/benchmarks/search", response_model=ApiResponse[BenchmarkSearchResponse])
async def benchmark_search(
    q: str = Query(min_length=2),
    service: MarketDataService = Depends(get_marketdata_service),
) -> ApiResponse[BenchmarkSearchResponse]:
    return ApiResponse(data=await _run_blocking(service.search_benchmarks, q))


@router.post("/marketdata/comparisons/series", response_model=ApiResponse[ComparisonSeriesResponse])
async def comparison_series(
    payload: ComparisonSeriesRequest,
    service: MarketDataService = Depends(get_marketdata_service),
) -> ApiResponse[ComparisonSeriesResponse]:
    return ApiResponse(data=await _run_blocking(service.get_comparison_series, payload))
