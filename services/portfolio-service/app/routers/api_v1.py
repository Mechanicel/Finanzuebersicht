from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from finanzuebersicht_shared.models import ApiResponse

from app.dependencies import get_portfolio_service
from app.models import (
    HoldingSnapshot,
    HoldingsReplaceRequest,
    HoldingsResponse,
    PortfolioDetailResponse,
    ResponseMode,
    SnapshotCreateRequest,
    SnapshotsResponse,
)
from app.service import PortfolioService

router = APIRouter(tags=["portfolio"])


@router.get("/portfolios/{portfolio_id}", response_model=ApiResponse[PortfolioDetailResponse])
async def get_portfolio(
    portfolio_id: UUID,
    include_history: bool = Query(default=False),
    response_mode: ResponseMode = Query(default=ResponseMode.DETAILED),
    service: PortfolioService = Depends(get_portfolio_service),
) -> ApiResponse[PortfolioDetailResponse]:
    return ApiResponse(data=service.get_portfolio(portfolio_id, include_history=include_history, mode=response_mode))


@router.get("/accounts/{account_id}/portfolio", response_model=ApiResponse[PortfolioDetailResponse])
async def get_account_portfolio(
    account_id: UUID,
    include_history: bool = Query(default=False),
    response_mode: ResponseMode = Query(default=ResponseMode.DETAILED),
    service: PortfolioService = Depends(get_portfolio_service),
) -> ApiResponse[PortfolioDetailResponse]:
    return ApiResponse(data=service.get_account_portfolio(account_id, include_history=include_history, mode=response_mode))


@router.put("/accounts/{account_id}/portfolio/holdings", response_model=ApiResponse[HoldingsResponse])
async def put_account_holdings(
    account_id: UUID,
    payload: HoldingsReplaceRequest,
    service: PortfolioService = Depends(get_portfolio_service),
) -> ApiResponse[HoldingsResponse]:
    return ApiResponse(data=service.put_holdings(account_id, payload))


@router.get("/accounts/{account_id}/portfolio/holdings", response_model=ApiResponse[HoldingsResponse])
async def get_account_holdings(
    account_id: UUID,
    response_mode: ResponseMode = Query(default=ResponseMode.DETAILED),
    service: PortfolioService = Depends(get_portfolio_service),
) -> ApiResponse[HoldingsResponse]:
    return ApiResponse(data=service.list_holdings(account_id, mode=response_mode))


@router.post(
    "/accounts/{account_id}/portfolio/snapshots",
    response_model=ApiResponse[HoldingSnapshot],
    status_code=status.HTTP_201_CREATED,
)
async def create_snapshot(
    account_id: UUID,
    payload: SnapshotCreateRequest,
    service: PortfolioService = Depends(get_portfolio_service),
) -> ApiResponse[HoldingSnapshot]:
    return ApiResponse(data=service.create_snapshot(account_id, payload))


@router.get("/accounts/{account_id}/portfolio/snapshots", response_model=ApiResponse[SnapshotsResponse])
async def list_snapshots(
    account_id: UUID,
    as_of: date | None = Query(default=None),
    include_history: bool = Query(default=True),
    response_mode: ResponseMode = Query(default=ResponseMode.DETAILED),
    service: PortfolioService = Depends(get_portfolio_service),
) -> ApiResponse[SnapshotsResponse]:
    return ApiResponse(
        data=service.list_snapshots(
            account_id,
            as_of=as_of,
            include_history=include_history,
            mode=response_mode,
        )
    )
