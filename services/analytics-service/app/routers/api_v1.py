from __future__ import annotations

from typing import Annotated
from uuid import UUID

import httpx
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
    PortfolioDashboardReadModel,
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
    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=504,
            detail={
                "error": "upstream_timeout",
                "message": "Abhängiger Service hat nicht rechtzeitig geantwortet.",
            },
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "error": "upstream_unavailable",
                "message": "Abhängiger Service ist derzeit nicht erreichbar.",
            },
        ) from exc
    except KeyError as exc:
        raise HTTPException(
            status_code=404, detail={"error": "person_not_found", "message": str(exc)}
        ) from exc


@router.get(
    "/analytics/persons/{person_id}/dashboard/overview",
    response_model=ApiResponse[DashboardSectionReadModel],
)
def dashboard_overview_section(
    person_id: UUID,
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> ApiResponse[DashboardSectionReadModel]:
    return ApiResponse(data=_call_or_404(lambda: service.get_dashboard_section(person_id, "overview")))


@router.get(
    "/analytics/persons/{person_id}/dashboard/allocation",
    response_model=ApiResponse[DashboardSectionReadModel],
)
def dashboard_allocation_section(
    person_id: UUID,
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> ApiResponse[DashboardSectionReadModel]:
    return ApiResponse(data=_call_or_404(lambda: service.get_dashboard_section(person_id, "allocation")))


@router.get(
    "/analytics/persons/{person_id}/dashboard/timeseries",
    response_model=ApiResponse[DashboardSectionReadModel],
)
def dashboard_timeseries_section(
    person_id: UUID,
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> ApiResponse[DashboardSectionReadModel]:
    return ApiResponse(data=_call_or_404(lambda: service.get_dashboard_section(person_id, "timeseries")))


@router.get(
    "/analytics/persons/{person_id}/dashboard/metrics",
    response_model=ApiResponse[DashboardSectionReadModel],
)
def dashboard_metrics_section(
    person_id: UUID,
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> ApiResponse[DashboardSectionReadModel]:
    return ApiResponse(data=_call_or_404(lambda: service.get_dashboard_section(person_id, "metrics")))


@router.get(
    "/analytics/persons/{person_id}/overview", response_model=ApiResponse[OverviewReadModel]
)
def overview(
    person_id: UUID,
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> ApiResponse[OverviewReadModel]:
    return ApiResponse(data=_call_or_404(lambda: service.overview(person_id)))


@router.get(
    "/analytics/persons/{person_id}/allocation", response_model=ApiResponse[AllocationReadModel]
)
def allocation(
    person_id: UUID,
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> ApiResponse[AllocationReadModel]:
    return ApiResponse(data=_call_or_404(lambda: service.allocation(person_id)))


@router.get(
    "/analytics/persons/{person_id}/timeseries", response_model=ApiResponse[TimeseriesReadModel]
)
def timeseries(
    person_id: UUID,
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> ApiResponse[TimeseriesReadModel]:
    return ApiResponse(data=_call_or_404(lambda: service.timeseries(person_id)))


@router.get(
    "/analytics/persons/{person_id}/monthly-comparison",
    response_model=ApiResponse[MonthlyComparisonReadModel],
)
def monthly_comparison(
    person_id: UUID,
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> ApiResponse[MonthlyComparisonReadModel]:
    return ApiResponse(data=_call_or_404(lambda: service.monthly_comparison(person_id)))


@router.get("/analytics/persons/{person_id}/metrics", response_model=ApiResponse[MetricsReadModel])
def metrics(
    person_id: UUID,
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> ApiResponse[MetricsReadModel]:
    return ApiResponse(data=_call_or_404(lambda: service.metrics(person_id)))


@router.get("/analytics/persons/{person_id}/heatmap", response_model=ApiResponse[HeatmapReadModel])
def heatmap(
    person_id: UUID,
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> ApiResponse[HeatmapReadModel]:
    return ApiResponse(data=_call_or_404(lambda: service.heatmap(person_id)))


@router.get(
    "/analytics/persons/{person_id}/forecast", response_model=ApiResponse[ForecastReadModel]
)
def forecast(
    person_id: UUID,
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> ApiResponse[ForecastReadModel]:
    return ApiResponse(data=_call_or_404(lambda: service.forecast(person_id)))


@router.get(
    "/analytics/persons/{person_id}/portfolio-dashboard",
    response_model=ApiResponse[PortfolioDashboardReadModel],
)
def portfolio_dashboard(
    person_id: UUID,
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    range: str = "3m",
) -> ApiResponse[PortfolioDashboardReadModel]:
    return ApiResponse(data=_call_or_404(lambda: service.portfolio_dashboard(person_id, range_value=range)))


@router.get(
    "/analytics/persons/{person_id}/portfolio-summary",
    response_model=ApiResponse[PortfolioSummaryReadModel],
)
def portfolio_summary(
    person_id: UUID,
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> ApiResponse[PortfolioSummaryReadModel]:
    return ApiResponse(data=_call_or_404(lambda: service.portfolio_summary(person_id)))


@router.get(
    "/analytics/persons/{person_id}/portfolio-performance",
    response_model=ApiResponse[PortfolioPerformanceReadModel],
)
def portfolio_performance(
    person_id: UUID,
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> ApiResponse[PortfolioPerformanceReadModel]:
    return ApiResponse(data=_call_or_404(lambda: service.portfolio_performance(person_id)))


@router.get(
    "/analytics/persons/{person_id}/portfolio-exposures",
    response_model=ApiResponse[PortfolioExposuresReadModel],
)
def portfolio_exposures(
    person_id: UUID,
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> ApiResponse[PortfolioExposuresReadModel]:
    return ApiResponse(data=_call_or_404(lambda: service.portfolio_exposures(person_id)))


@router.get(
    "/analytics/persons/{person_id}/portfolio-holdings",
    response_model=ApiResponse[PortfolioHoldingsReadModel],
)
def portfolio_holdings(
    person_id: UUID,
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> ApiResponse[PortfolioHoldingsReadModel]:
    return ApiResponse(data=_call_or_404(lambda: service.portfolio_holdings(person_id)))


@router.get(
    "/analytics/persons/{person_id}/portfolio-risk",
    response_model=ApiResponse[PortfolioRiskReadModel],
)
def portfolio_risk(
    person_id: UUID,
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    range: str = "3m",
) -> ApiResponse[PortfolioRiskReadModel]:
    return ApiResponse(data=_call_or_404(lambda: service.portfolio_risk(person_id, range_value=range)))


@router.get(
    "/analytics/persons/{person_id}/portfolio-contributors",
    response_model=ApiResponse[PortfolioContributorsReadModel],
)
def portfolio_contributors(
    person_id: UUID,
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    range: str = "3m",
) -> ApiResponse[PortfolioContributorsReadModel]:
    return ApiResponse(data=_call_or_404(lambda: service.portfolio_contributors(person_id, range_value=range)))


@router.get(
    "/analytics/persons/{person_id}/portfolio-data-coverage",
    response_model=ApiResponse[PortfolioDataCoverageReadModel],
)
def portfolio_data_coverage(
    person_id: UUID,
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> ApiResponse[PortfolioDataCoverageReadModel]:
    return ApiResponse(data=_call_or_404(lambda: service.portfolio_data_coverage(person_id)))
