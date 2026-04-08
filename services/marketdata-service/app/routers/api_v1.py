from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from finanzuebersicht_shared.models import ApiResponse

from app.dependencies import get_marketdata_service
from app.models import (
    BatchHistoryResponse,
    BatchPricesResponse,
    HoldingsSummaryResponse,
    InstrumentHistoryResponse,
    InstrumentPriceRefreshResponse,
    InstrumentProfile,
    InstrumentSearchResponse,
)
from app.service import MarketDataService

router = APIRouter(tags=["marketdata"])


@router.get("/marketdata/instruments/search", response_model=ApiResponse[InstrumentSearchResponse])
async def instrument_search(
    q: str = Query(min_length=1),
    limit: int = Query(default=10, ge=1, le=20),
    service: MarketDataService = Depends(get_marketdata_service),
) -> ApiResponse[InstrumentSearchResponse]:
    return ApiResponse(data=service.search_instruments(query=q, limit=limit))


@router.get("/marketdata/instruments/{symbol}/profile", response_model=ApiResponse[InstrumentProfile])
async def instrument_profile(
    symbol: str,
    service: MarketDataService = Depends(get_marketdata_service),
) -> ApiResponse[InstrumentProfile]:
    return ApiResponse(data=service.get_instrument_profile(symbol))


@router.get("/marketdata/depot/holdings-summary", response_model=ApiResponse[HoldingsSummaryResponse])
async def holdings_summary(
    symbols: str = Query(..., min_length=1),
    service: MarketDataService = Depends(get_marketdata_service),
) -> ApiResponse[HoldingsSummaryResponse]:
    return ApiResponse(data=service.get_holdings_summary(symbols))


@router.get("/marketdata/batch/prices", response_model=ApiResponse[BatchPricesResponse])
async def batch_prices(
    symbols: str = Query(..., min_length=1),
    service: MarketDataService = Depends(get_marketdata_service),
) -> ApiResponse[BatchPricesResponse]:
    return ApiResponse(data=service.get_batch_prices(symbols))


@router.get("/marketdata/batch/history", response_model=ApiResponse[BatchHistoryResponse])
async def batch_history(
    symbols: str = Query(..., min_length=1),
    range_value: str = Query(default="3m", alias="range"),
    service: MarketDataService = Depends(get_marketdata_service),
) -> ApiResponse[BatchHistoryResponse]:
    return ApiResponse(data=service.get_batch_history(symbols, range_value))


@router.get("/marketdata/instruments/{symbol}/snapshot", response_model=ApiResponse[dict])
async def instrument_snapshot(
    symbol: str,
    service: MarketDataService = Depends(get_marketdata_service),
) -> ApiResponse[dict]:
    return ApiResponse(data=service.get_instrument_snapshot(symbol))


@router.get("/marketdata/instruments/{symbol}/full", response_model=ApiResponse[dict])
async def instrument_full(
    symbol: str,
    service: MarketDataService = Depends(get_marketdata_service),
) -> ApiResponse[dict]:
    return ApiResponse(data=service.get_instrument_full(symbol))


@router.get("/marketdata/instruments/{symbol}/fundamentals", response_model=ApiResponse[dict])
async def instrument_fundamentals(
    symbol: str,
    service: MarketDataService = Depends(get_marketdata_service),
) -> ApiResponse[dict]:
    return ApiResponse(data=service.get_instrument_fundamentals(symbol))


@router.get("/marketdata/instruments/{symbol}/metrics", response_model=ApiResponse[dict])
async def instrument_metrics(
    symbol: str,
    service: MarketDataService = Depends(get_marketdata_service),
) -> ApiResponse[dict]:
    return ApiResponse(data=service.get_instrument_metrics(symbol))


@router.get("/marketdata/instruments/{symbol}/financials", response_model=ApiResponse[dict])
async def instrument_financials(
    symbol: str,
    period: str = Query(default="annual"),
    service: MarketDataService = Depends(get_marketdata_service),
) -> ApiResponse[dict]:
    return ApiResponse(data=service.get_instrument_financials(symbol, period))


@router.get("/marketdata/instruments/{symbol}/risk", response_model=ApiResponse[dict])
async def instrument_risk(
    symbol: str,
    benchmark: str | None = Query(default=None),
    service: MarketDataService = Depends(get_marketdata_service),
) -> ApiResponse[dict]:
    return ApiResponse(data=service.get_instrument_risk(symbol, benchmark))


@router.get("/marketdata/instruments/{symbol}/benchmark", response_model=ApiResponse[dict])
async def instrument_benchmark(
    symbol: str,
    benchmark: str | None = Query(default=None),
    service: MarketDataService = Depends(get_marketdata_service),
) -> ApiResponse[dict]:
    return ApiResponse(data=service.get_instrument_benchmark(symbol, benchmark))


@router.get("/marketdata/instruments/{symbol}/timeseries", response_model=ApiResponse[dict])
async def instrument_timeseries(
    symbol: str,
    series: str | None = Query(default=None),
    benchmark: str | None = Query(default=None),
    service: MarketDataService = Depends(get_marketdata_service),
) -> ApiResponse[dict]:
    return ApiResponse(data=service.get_instrument_timeseries(symbol, series, benchmark))


@router.get("/marketdata/instruments/{symbol}/comparison-timeseries", response_model=ApiResponse[dict])
async def instrument_comparison_timeseries(
    symbol: str,
    symbols: str = Query(..., min_length=1),
    service: MarketDataService = Depends(get_marketdata_service),
) -> ApiResponse[dict]:
    return ApiResponse(data=service.get_instrument_comparison_timeseries(symbol, symbols))


@router.get("/marketdata/benchmark-catalog", response_model=ApiResponse[dict])
async def benchmark_catalog(
    service: MarketDataService = Depends(get_marketdata_service),
) -> ApiResponse[dict]:
    return ApiResponse(data=service.get_benchmark_catalog())


@router.get("/marketdata/benchmark-search", response_model=ApiResponse[dict])
async def benchmark_search(
    q: str = Query(..., min_length=1),
    service: MarketDataService = Depends(get_marketdata_service),
) -> ApiResponse[dict]:
    return ApiResponse(data=service.search_benchmark_catalog(q))


@router.get("/marketdata/instruments/{symbol}/history", response_model=ApiResponse[InstrumentHistoryResponse])
async def instrument_history(
    symbol: str,
    range_value: str = Query(default="3m", alias="range"),
    service: MarketDataService = Depends(get_marketdata_service),
) -> ApiResponse[InstrumentHistoryResponse]:
    return ApiResponse(data=service.get_instrument_history(symbol, range_value))


@router.post(
    "/marketdata/instruments/{symbol}/refresh-price",
    response_model=ApiResponse[InstrumentPriceRefreshResponse],
)
async def refresh_instrument_price(
    symbol: str,
    background_tasks: BackgroundTasks,
    service: MarketDataService = Depends(get_marketdata_service),
) -> ApiResponse[InstrumentPriceRefreshResponse]:
    response = service.refresh_instrument_price(symbol)
    if response.history_action == "seed_max_in_background":
        background_tasks.add_task(service.seed_history_max, response.symbol)
    else:
        background_tasks.add_task(service.enrich_history_recent, response.symbol)
    return ApiResponse(data=response)
