from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from finanzuebersicht_shared.models import ApiResponse

from app.dependencies import get_marketdata_service
from app.models import InstrumentProfile, InstrumentSearchResponse
from app.service import MarketDataService

router = APIRouter(tags=["marketdata"])


@router.get("/marketdata/instruments/search", response_model=ApiResponse[InstrumentSearchResponse])
async def instrument_search(
    q: str = Query(min_length=1),
    limit: int = Query(default=10, ge=1, le=25),
    service: MarketDataService = Depends(get_marketdata_service),
) -> ApiResponse[InstrumentSearchResponse]:
    return ApiResponse(data=service.search_instruments(query=q, limit=limit))


@router.get("/marketdata/instruments/{symbol}/profile", response_model=ApiResponse[InstrumentProfile])
async def instrument_profile(
    symbol: str,
    service: MarketDataService = Depends(get_marketdata_service),
) -> ApiResponse[InstrumentProfile]:
    return ApiResponse(data=service.get_instrument_profile(symbol))
