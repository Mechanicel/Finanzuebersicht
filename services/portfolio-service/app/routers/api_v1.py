from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from finanzuebersicht_shared.models import ApiResponse

from app.dependencies import get_portfolio_service
from app.models import (
    Holding,
    HoldingCreatePayload,
    HoldingUpdatePayload,
    Portfolio,
    PortfolioCreatePayload,
    PortfolioDetailResponse,
    PortfolioListResponse,
)
from app.service import PortfolioService

router = APIRouter(tags=["portfolio"])


@router.post("/portfolios", response_model=ApiResponse[Portfolio], status_code=status.HTTP_201_CREATED)
async def create_portfolio(
    payload: PortfolioCreatePayload,
    service: PortfolioService = Depends(get_portfolio_service),
) -> ApiResponse[Portfolio]:
    return ApiResponse(data=service.create_portfolio(payload))


@router.get("/persons/{person_id}/portfolios", response_model=ApiResponse[PortfolioListResponse])
async def list_person_portfolios(
    person_id: UUID,
    service: PortfolioService = Depends(get_portfolio_service),
) -> ApiResponse[PortfolioListResponse]:
    return ApiResponse(data=service.list_person_portfolios(person_id))


@router.get("/portfolios/{portfolio_id}", response_model=ApiResponse[PortfolioDetailResponse])
async def get_portfolio(
    portfolio_id: UUID,
    service: PortfolioService = Depends(get_portfolio_service),
) -> ApiResponse[PortfolioDetailResponse]:
    return ApiResponse(data=service.get_portfolio_detail(portfolio_id))


@router.post(
    "/portfolios/{portfolio_id}/holdings",
    response_model=ApiResponse[Holding],
    status_code=status.HTTP_201_CREATED,
)
async def create_holding(
    portfolio_id: UUID,
    payload: HoldingCreatePayload,
    service: PortfolioService = Depends(get_portfolio_service),
) -> ApiResponse[Holding]:
    return ApiResponse(data=service.create_holding(portfolio_id, payload))


@router.patch("/portfolios/{portfolio_id}/holdings/{holding_id}", response_model=ApiResponse[Holding])
async def update_holding(
    portfolio_id: UUID,
    holding_id: UUID,
    payload: HoldingUpdatePayload,
    service: PortfolioService = Depends(get_portfolio_service),
) -> ApiResponse[Holding]:
    return ApiResponse(data=service.update_holding(portfolio_id, holding_id, payload))


@router.delete("/portfolios/{portfolio_id}/holdings/{holding_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_holding(
    portfolio_id: UUID,
    holding_id: UUID,
    service: PortfolioService = Depends(get_portfolio_service),
) -> Response:
    service.delete_holding(portfolio_id, holding_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
