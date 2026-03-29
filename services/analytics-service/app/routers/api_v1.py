from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from finanzuebersicht_shared.models import ApiResponse

from app.dependencies import get_analytics_service
from app.models import (
    AllocationReadModel,
    ForecastReadModel,
    HeatmapReadModel,
    MetricsReadModel,
    MonthlyComparisonReadModel,
    OverviewReadModel,
    TimeseriesReadModel,
)
from app.service import AnalyticsService

router = APIRouter(tags=["analytics"])


def _call_or_404(fn):
    try:
        return fn()
    except KeyError as exc:
        raise HTTPException(
            status_code=404, detail={"error": "person_not_found", "message": str(exc)}
        ) from exc


@router.get(
    "/analytics/persons/{person_id}/overview", response_model=ApiResponse[OverviewReadModel]
)
async def overview(
    person_id: UUID,
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> ApiResponse[OverviewReadModel]:
    return ApiResponse(data=_call_or_404(lambda: service.overview(person_id)))


@router.get(
    "/analytics/persons/{person_id}/allocation", response_model=ApiResponse[AllocationReadModel]
)
async def allocation(
    person_id: UUID,
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> ApiResponse[AllocationReadModel]:
    return ApiResponse(data=_call_or_404(lambda: service.allocation(person_id)))


@router.get(
    "/analytics/persons/{person_id}/timeseries", response_model=ApiResponse[TimeseriesReadModel]
)
async def timeseries(
    person_id: UUID,
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> ApiResponse[TimeseriesReadModel]:
    return ApiResponse(data=_call_or_404(lambda: service.timeseries(person_id)))


@router.get(
    "/analytics/persons/{person_id}/monthly-comparison",
    response_model=ApiResponse[MonthlyComparisonReadModel],
)
async def monthly_comparison(
    person_id: UUID,
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> ApiResponse[MonthlyComparisonReadModel]:
    return ApiResponse(data=_call_or_404(lambda: service.monthly_comparison(person_id)))


@router.get("/analytics/persons/{person_id}/metrics", response_model=ApiResponse[MetricsReadModel])
async def metrics(
    person_id: UUID,
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> ApiResponse[MetricsReadModel]:
    return ApiResponse(data=_call_or_404(lambda: service.metrics(person_id)))


@router.get("/analytics/persons/{person_id}/heatmap", response_model=ApiResponse[HeatmapReadModel])
async def heatmap(
    person_id: UUID,
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> ApiResponse[HeatmapReadModel]:
    return ApiResponse(data=_call_or_404(lambda: service.heatmap(person_id)))


@router.get(
    "/analytics/persons/{person_id}/forecast", response_model=ApiResponse[ForecastReadModel]
)
async def forecast(
    person_id: UUID,
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> ApiResponse[ForecastReadModel]:
    return ApiResponse(data=_call_or_404(lambda: service.forecast(person_id)))
