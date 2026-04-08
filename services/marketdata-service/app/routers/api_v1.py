from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from finanzuebersicht_shared.models import ApiResponse

from app.dependencies import get_marketdata_service
from app.models import InstrumentPriceRefreshResponse, InstrumentProfile, InstrumentSearchResponse
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
