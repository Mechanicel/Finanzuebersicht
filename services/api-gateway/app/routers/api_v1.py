from __future__ import annotations

from typing import Annotated
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException
from finanzuebersicht_shared.models import ApiResponse

from app.dependencies import get_gateway_service
from app.models import (
    AccountReadModel,
    DashboardReadModel,
    GatewayHealthReadModel,
    PersonListReadModel,
    PortfolioReadModel,
)
from app.service import GatewayService

router = APIRouter(tags=["app"])


@router.get("/app/persons", response_model=ApiResponse[PersonListReadModel])
async def list_persons(
    service: Annotated[GatewayService, Depends(get_gateway_service)],
) -> ApiResponse[PersonListReadModel]:
    return ApiResponse(data=await service.list_persons())


@router.get("/app/persons/{person_id}/dashboard", response_model=ApiResponse[DashboardReadModel])
async def dashboard(
    person_id: UUID, service: Annotated[GatewayService, Depends(get_gateway_service)]
) -> ApiResponse[DashboardReadModel]:
    try:
        return ApiResponse(data=await service.get_dashboard(person_id))
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=exc.response.status_code, detail={"error": "analytics_error"}
        ) from exc


@router.get("/app/persons/{person_id}/accounts", response_model=ApiResponse[list[AccountReadModel]])
async def accounts(
    person_id: UUID, service: Annotated[GatewayService, Depends(get_gateway_service)]
) -> ApiResponse[list[AccountReadModel]]:
    return ApiResponse(data=await service.list_accounts(person_id))


@router.get(
    "/app/persons/{person_id}/portfolios", response_model=ApiResponse[list[PortfolioReadModel]]
)
async def portfolios(
    person_id: UUID, service: Annotated[GatewayService, Depends(get_gateway_service)]
) -> ApiResponse[list[PortfolioReadModel]]:
    return ApiResponse(data=await service.list_portfolios(person_id))


@router.get("/app/persons/{person_id}/analytics/overview", response_model=ApiResponse[dict])
async def analytics_overview(
    person_id: UUID, service: Annotated[GatewayService, Depends(get_gateway_service)]
) -> ApiResponse[dict]:
    try:
        return ApiResponse(data=await service.get_analytics_overview(person_id))
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=exc.response.status_code, detail={"error": "analytics_error"}
        ) from exc


@router.get("/app/persons/{person_id}/health", response_model=ApiResponse[GatewayHealthReadModel])
async def app_health(
    person_id: UUID, service: Annotated[GatewayService, Depends(get_gateway_service)]
) -> ApiResponse[GatewayHealthReadModel]:
    return ApiResponse(data=await service.dependency_health(person_id))
