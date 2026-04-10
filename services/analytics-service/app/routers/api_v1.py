from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from finanzuebersicht_shared.models import ApiResponse

from app.dependencies import get_analytics_service
from app.models import (
    AllocationReadModel,
    DashboardSectionReadModel,
    ForecastReadModel,
    HeatmapReadModel,
    MetricsReadModel,
    MonthlyComparisonReadModel,
    OverviewReadModel,
    PortfolioContributorsReadModel,
    PortfolioDataCoverageReadModel,
    PortfolioExposuresReadModel,
    PortfolioHoldingsReadModel,
    PortfolioPerformanceReadModel,
    PortfolioRiskReadModel,
    PortfolioSummaryReadModel,
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
    "/analytics/persons/{person_id}/dashboard/overview",
    response_model=ApiResponse[DashboardSectionReadModel],
)
async def dashboard_overview_section(
    person_id: UUID,
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> ApiResponse[DashboardSectionReadModel]:
    return ApiResponse(data=_call_or_404(lambda: service.get_dashboard_section(person_id, "overview")))


@router.get(
    "/analytics/persons/{person_id}/dashboard/allocation",
    response_model=ApiResponse[DashboardSectionReadModel],
)
async def dashboard_allocation_section(
    person_id: UUID,
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> ApiResponse[DashboardSectionReadModel]:
    return ApiResponse(data=_call_or_404(lambda: service.get_dashboard_section(person_id, "allocation")))


@router.get(
    "/analytics/persons/{person_id}/dashboard/timeseries",
    response_model=ApiResponse[DashboardSectionReadModel],
)
async def dashboard_timeseries_section(
    person_id: UUID,
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> ApiResponse[DashboardSectionReadModel]:
    return ApiResponse(data=_call_or_404(lambda: service.get_dashboard_section(person_id, "timeseries")))


@router.get(
    "/analytics/persons/{person_id}/dashboard/metrics",
    response_model=ApiResponse[DashboardSectionReadModel],
)
async def dashboard_metrics_section(
    person_id: UUID,
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> ApiResponse[DashboardSectionReadModel]:
    return ApiResponse(data=_call_or_404(lambda: service.get_dashboard_section(person_id, "metrics")))


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


@router.get(
    "/analytics/persons/{person_id}/portfolio-summary",
    response_model=ApiResponse[PortfolioSummaryReadModel],
)
async def portfolio_summary(
    person_id: UUID,
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> ApiResponse[PortfolioSummaryReadModel]:
    return ApiResponse(data=_call_or_404(lambda: service.portfolio_summary(person_id)))


@router.get(
    "/analytics/persons/{person_id}/portfolio-performance",
    response_model=ApiResponse[PortfolioPerformanceReadModel],
)
async def portfolio_performance(
    person_id: UUID,
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> ApiResponse[PortfolioPerformanceReadModel]:
    return ApiResponse(data=_call_or_404(lambda: service.portfolio_performance(person_id)))


@router.get(
    "/analytics/persons/{person_id}/portfolio-exposures",
    response_model=ApiResponse[PortfolioExposuresReadModel],
)
async def portfolio_exposures(
    person_id: UUID,
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> ApiResponse[PortfolioExposuresReadModel]:
    return ApiResponse(data=_call_or_404(lambda: service.portfolio_exposures(person_id)))


@router.get(
    "/analytics/persons/{person_id}/portfolio-holdings",
    response_model=ApiResponse[PortfolioHoldingsReadModel],
)
async def portfolio_holdings(
    person_id: UUID,
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> ApiResponse[PortfolioHoldingsReadModel]:
    return ApiResponse(data=_call_or_404(lambda: service.portfolio_holdings(person_id)))


@router.get(
    "/analytics/persons/{person_id}/portfolio-risk",
    response_model=ApiResponse[PortfolioRiskReadModel],
)
async def portfolio_risk(
    person_id: UUID,
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> ApiResponse[PortfolioRiskReadModel]:
    return ApiResponse(data=_call_or_404(lambda: service.portfolio_risk(person_id)))


@router.get(
    "/analytics/persons/{person_id}/portfolio-contributors",
    response_model=ApiResponse[PortfolioContributorsReadModel],
)
async def portfolio_contributors(
    person_id: UUID,
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> ApiResponse[PortfolioContributorsReadModel]:
    return ApiResponse(data=_call_or_404(lambda: service.portfolio_contributors(person_id)))


@router.get(
    "/analytics/persons/{person_id}/portfolio-data-coverage",
    response_model=ApiResponse[PortfolioDataCoverageReadModel],
)
async def portfolio_data_coverage(
    person_id: UUID,
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> ApiResponse[PortfolioDataCoverageReadModel]:
    return ApiResponse(data=_call_or_404(lambda: service.portfolio_data_coverage(person_id)))
