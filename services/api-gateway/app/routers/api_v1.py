from __future__ import annotations

from typing import Annotated, Literal
from uuid import UUID

import httpx
import logging
import time
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from finanzuebersicht_shared.models import ApiResponse

from app.dependencies import get_gateway_service
from app.models import (
    AccountCreatePayload,
    AccountReadModel,
    AccountUpdatePayload,
    AllowanceListReadModel,
    AllowanceSummaryReadModel,
    AllowanceUpsertPayload,
    AssignmentListReadModel,
    BankCreatePayload,
    BankListReadModel,
    BankReadModel,
    DashboardReadModel,
    GatewayHealthReadModel,
    PersonCreatePayload,
    PersonDetailReadModel,
    PersonListReadModel,
    PersonReadModel,
    PersonBankAssignmentReadModel,
    PersonUpdatePayload,
    PortfolioContributorsReadModel,
    PortfolioDashboardReadModel,
    PortfolioCreatePayload,
    PortfolioDataCoverageReadModel,
    PortfolioDetailReadModel,
    PortfolioExposuresReadModel,
    PortfolioHoldingsReadModel,
    PortfolioListReadModel,
    PortfolioPerformanceReadModel,
    PortfolioReadModel,
    PortfolioRiskReadModel,
    PortfolioSummaryReadModel,
    HoldingCreatePayload,
    HoldingsRefreshStubReadModel,
    HoldingReadModel,
    HoldingUpdatePayload,
    MarketdataProfileReadModel,
    TaxAllowanceReadModel,
)
from app.service import GatewayService

router = APIRouter(tags=["app"])
LOGGER = logging.getLogger(__name__)


@router.get("/app/persons", response_model=ApiResponse[PersonListReadModel])
async def list_persons(
    service: Annotated[GatewayService, Depends(get_gateway_service)],
    q: str | None = Query(default=None),
    sort_by: str | None = Query(default=None),
    direction: str | None = Query(default=None),
    limit: int | None = Query(default=None),
    offset: int | None = Query(default=None),
) -> ApiResponse[PersonListReadModel]:
    return ApiResponse(
        data=await service.list_persons(
            q=q,
            sort_by=sort_by,
            direction=direction,
            limit=limit,
            offset=offset,
        )
    )


@router.post("/app/persons", response_model=ApiResponse[PersonReadModel], status_code=status.HTTP_201_CREATED)
async def create_person(
    payload: PersonCreatePayload,
    service: Annotated[GatewayService, Depends(get_gateway_service)],
) -> ApiResponse[PersonReadModel]:
    return ApiResponse(data=await service.create_person(payload))


@router.get("/app/persons/{person_id}", response_model=ApiResponse[PersonDetailReadModel])
async def get_person(
    person_id: UUID,
    service: Annotated[GatewayService, Depends(get_gateway_service)],
) -> ApiResponse[PersonDetailReadModel]:
    return ApiResponse(data=await service.get_person(person_id))


@router.patch("/app/persons/{person_id}", response_model=ApiResponse[PersonReadModel])
async def update_person(
    person_id: UUID,
    payload: PersonUpdatePayload,
    service: Annotated[GatewayService, Depends(get_gateway_service)],
) -> ApiResponse[PersonReadModel]:
    return ApiResponse(data=await service.update_person(person_id, payload))


@router.delete("/app/persons/{person_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_person(
    person_id: UUID,
    service: Annotated[GatewayService, Depends(get_gateway_service)],
) -> Response:
    await service.delete_person(person_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/app/persons/{person_id}/banks", response_model=ApiResponse[AssignmentListReadModel])
async def list_person_banks(
    person_id: UUID,
    service: Annotated[GatewayService, Depends(get_gateway_service)],
) -> ApiResponse[AssignmentListReadModel]:
    return ApiResponse(data=await service.list_person_banks(person_id))


@router.post(
    "/app/persons/{person_id}/banks/{bank_id}",
    response_model=ApiResponse[PersonBankAssignmentReadModel],
    status_code=status.HTTP_201_CREATED,
)
async def assign_person_bank(
    person_id: UUID,
    bank_id: UUID,
    service: Annotated[GatewayService, Depends(get_gateway_service)],
) -> ApiResponse[PersonBankAssignmentReadModel]:
    return ApiResponse(data=await service.assign_bank(person_id, bank_id))


@router.delete("/app/persons/{person_id}/banks/{bank_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unassign_person_bank(
    person_id: UUID,
    bank_id: UUID,
    service: Annotated[GatewayService, Depends(get_gateway_service)],
) -> Response:
    await service.unassign_bank(person_id, bank_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/app/persons/{person_id}/allowances", response_model=ApiResponse[AllowanceListReadModel])
async def list_allowances(
    person_id: UUID,
    service: Annotated[GatewayService, Depends(get_gateway_service)],
    tax_year: int | None = Query(default=None),
) -> ApiResponse[AllowanceListReadModel]:
    return ApiResponse(data=await service.list_allowances(person_id, tax_year=tax_year))


@router.put("/app/persons/{person_id}/allowances/{bank_id}", response_model=ApiResponse[TaxAllowanceReadModel])
async def set_allowance(
    person_id: UUID,
    bank_id: UUID,
    payload: AllowanceUpsertPayload,
    service: Annotated[GatewayService, Depends(get_gateway_service)],
) -> ApiResponse[TaxAllowanceReadModel]:
    return ApiResponse(data=await service.set_allowance(person_id, bank_id, payload))


@router.get("/app/persons/{person_id}/allowances/summary", response_model=ApiResponse[AllowanceSummaryReadModel])
async def allowance_summary(
    person_id: UUID,
    service: Annotated[GatewayService, Depends(get_gateway_service)],
    tax_year: int = Query(...),
) -> ApiResponse[AllowanceSummaryReadModel]:
    return ApiResponse(data=await service.allowance_summary(person_id, tax_year=tax_year))




@router.get("/app/banks", response_model=ApiResponse[BankListReadModel])
async def list_banks(service: Annotated[GatewayService, Depends(get_gateway_service)]) -> ApiResponse[BankListReadModel]:
    return ApiResponse(data=await service.list_banks())


@router.post("/app/banks", response_model=ApiResponse[BankReadModel], status_code=status.HTTP_201_CREATED)
async def create_bank(
    payload: BankCreatePayload,
    service: Annotated[GatewayService, Depends(get_gateway_service)],
) -> ApiResponse[BankReadModel]:
    return ApiResponse(data=await service.create_bank(payload))

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


@router.get("/app/persons/{person_id}/dashboard/overview", response_model=ApiResponse[dict])
async def dashboard_overview_section(
    person_id: UUID, service: Annotated[GatewayService, Depends(get_gateway_service)]
) -> ApiResponse[dict]:
    return ApiResponse(data=await service.get_dashboard_section(person_id, "overview"))


@router.get("/app/persons/{person_id}/dashboard/allocation", response_model=ApiResponse[dict])
async def dashboard_allocation_section(
    person_id: UUID, service: Annotated[GatewayService, Depends(get_gateway_service)]
) -> ApiResponse[dict]:
    return ApiResponse(data=await service.get_dashboard_section(person_id, "allocation"))


@router.get("/app/persons/{person_id}/dashboard/timeseries", response_model=ApiResponse[dict])
async def dashboard_timeseries_section(
    person_id: UUID, service: Annotated[GatewayService, Depends(get_gateway_service)]
) -> ApiResponse[dict]:
    return ApiResponse(data=await service.get_dashboard_section(person_id, "timeseries"))


@router.get("/app/persons/{person_id}/dashboard/metrics", response_model=ApiResponse[dict])
async def dashboard_metrics_section(
    person_id: UUID, service: Annotated[GatewayService, Depends(get_gateway_service)]
) -> ApiResponse[dict]:
    return ApiResponse(data=await service.get_dashboard_section(person_id, "metrics"))


@router.get("/app/persons/{person_id}/portfolio-summary", response_model=ApiResponse[PortfolioSummaryReadModel])
async def portfolio_summary(
    person_id: UUID, service: Annotated[GatewayService, Depends(get_gateway_service)]
) -> ApiResponse[PortfolioSummaryReadModel]:
    return ApiResponse(data=await service.get_portfolio_summary(person_id))


@router.get("/app/persons/{person_id}/portfolio-dashboard", response_model=ApiResponse[PortfolioDashboardReadModel])
async def portfolio_dashboard(
    person_id: UUID,
    service: Annotated[GatewayService, Depends(get_gateway_service)],
    range: str = Query(default="3m"),
) -> ApiResponse[PortfolioDashboardReadModel]:
    return ApiResponse(data=await service.get_portfolio_dashboard(person_id, range_value=range))


@router.get(
    "/app/persons/{person_id}/portfolio-performance",
    response_model=ApiResponse[PortfolioPerformanceReadModel],
)
async def portfolio_performance(
    person_id: UUID, service: Annotated[GatewayService, Depends(get_gateway_service)]
) -> ApiResponse[PortfolioPerformanceReadModel]:
    return ApiResponse(data=await service.get_portfolio_performance(person_id))


@router.get(
    "/app/persons/{person_id}/portfolio-exposures",
    response_model=ApiResponse[PortfolioExposuresReadModel],
)
async def portfolio_exposures(
    person_id: UUID, service: Annotated[GatewayService, Depends(get_gateway_service)]
) -> ApiResponse[PortfolioExposuresReadModel]:
    return ApiResponse(data=await service.get_portfolio_exposures(person_id))


@router.get(
    "/app/persons/{person_id}/portfolio-holdings",
    response_model=ApiResponse[PortfolioHoldingsReadModel],
)
async def portfolio_holdings(
    person_id: UUID, service: Annotated[GatewayService, Depends(get_gateway_service)]
) -> ApiResponse[PortfolioHoldingsReadModel]:
    return ApiResponse(data=await service.get_portfolio_holdings(person_id))


@router.get("/app/persons/{person_id}/portfolio-risk", response_model=ApiResponse[PortfolioRiskReadModel])
async def portfolio_risk(
    person_id: UUID, service: Annotated[GatewayService, Depends(get_gateway_service)]
) -> ApiResponse[PortfolioRiskReadModel]:
    return ApiResponse(data=await service.get_portfolio_risk(person_id))


@router.get(
    "/app/persons/{person_id}/portfolio-contributors",
    response_model=ApiResponse[PortfolioContributorsReadModel],
)
async def portfolio_contributors(
    person_id: UUID,
    service: Annotated[GatewayService, Depends(get_gateway_service)],
    range: str = Query(default="3m"),
) -> ApiResponse[PortfolioContributorsReadModel]:
    return ApiResponse(data=await service.get_portfolio_contributors(person_id, range_value=range))


@router.get(
    "/app/persons/{person_id}/portfolio-data-coverage",
    response_model=ApiResponse[PortfolioDataCoverageReadModel],
)
async def portfolio_data_coverage(
    person_id: UUID, service: Annotated[GatewayService, Depends(get_gateway_service)]
) -> ApiResponse[PortfolioDataCoverageReadModel]:
    return ApiResponse(data=await service.get_portfolio_data_coverage(person_id))


@router.get("/app/persons/{person_id}/accounts", response_model=ApiResponse[list[AccountReadModel]])
async def accounts(
    person_id: UUID, service: Annotated[GatewayService, Depends(get_gateway_service)]
) -> ApiResponse[list[AccountReadModel]]:
    return ApiResponse(data=await service.list_accounts(person_id))


@router.get("/app/persons/{person_id}/accounts/{account_id}", response_model=ApiResponse[AccountReadModel])
async def get_account(
    person_id: UUID,
    account_id: UUID,
    service: Annotated[GatewayService, Depends(get_gateway_service)],
) -> ApiResponse[AccountReadModel]:
    return ApiResponse(data=await service.get_account(person_id, account_id))


@router.post("/app/persons/{person_id}/accounts", response_model=ApiResponse[AccountReadModel], status_code=status.HTTP_201_CREATED)
async def create_account(
    person_id: UUID,
    payload: AccountCreatePayload,
    service: Annotated[GatewayService, Depends(get_gateway_service)],
) -> ApiResponse[AccountReadModel]:
    return ApiResponse(data=await service.create_account(person_id, payload))


@router.patch("/app/persons/{person_id}/accounts/{account_id}", response_model=ApiResponse[AccountReadModel])
async def patch_account(
    person_id: UUID,
    account_id: UUID,
    payload: AccountUpdatePayload,
    service: Annotated[GatewayService, Depends(get_gateway_service)],
) -> ApiResponse[AccountReadModel]:
    return ApiResponse(data=await service.update_account(person_id, account_id, payload))




@router.delete("/app/persons/{person_id}/accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    person_id: UUID,
    account_id: UUID,
    service: Annotated[GatewayService, Depends(get_gateway_service)],
) -> Response:
    await service.delete_account(person_id, account_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/app/persons/{person_id}/portfolios", response_model=ApiResponse[PortfolioListReadModel])
async def portfolios(
    person_id: UUID, service: Annotated[GatewayService, Depends(get_gateway_service)]
) -> ApiResponse[PortfolioListReadModel]:
    return ApiResponse(data=await service.list_portfolios(person_id))


@router.post("/app/persons/{person_id}/portfolios", response_model=ApiResponse[PortfolioReadModel], status_code=status.HTTP_201_CREATED)
async def create_portfolio(
    person_id: UUID,
    payload: PortfolioCreatePayload,
    service: Annotated[GatewayService, Depends(get_gateway_service)],
) -> ApiResponse[PortfolioReadModel]:
    return ApiResponse(data=await service.create_portfolio(person_id, payload))


@router.get("/app/portfolios/{portfolio_id}", response_model=ApiResponse[PortfolioDetailReadModel])
async def portfolio_detail(
    portfolio_id: UUID,
    service: Annotated[GatewayService, Depends(get_gateway_service)],
) -> ApiResponse[PortfolioDetailReadModel]:
    return ApiResponse(data=await service.get_portfolio(portfolio_id))


@router.post("/app/portfolios/{portfolio_id}/holdings", response_model=ApiResponse[HoldingReadModel], status_code=status.HTTP_201_CREATED)
async def add_holding(
    portfolio_id: UUID,
    payload: HoldingCreatePayload,
    service: Annotated[GatewayService, Depends(get_gateway_service)],
) -> ApiResponse[HoldingReadModel]:
    return ApiResponse(data=await service.create_holding(portfolio_id, payload))


@router.patch("/app/portfolios/{portfolio_id}/holdings/{holding_id}", response_model=ApiResponse[HoldingReadModel])
async def patch_holding(
    portfolio_id: UUID,
    holding_id: UUID,
    payload: HoldingUpdatePayload,
    service: Annotated[GatewayService, Depends(get_gateway_service)],
) -> ApiResponse[HoldingReadModel]:
    return ApiResponse(data=await service.update_holding(portfolio_id, holding_id, payload))


@router.delete("/app/portfolios/{portfolio_id}/holdings/{holding_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_holding(
    portfolio_id: UUID,
    holding_id: UUID,
    service: Annotated[GatewayService, Depends(get_gateway_service)],
) -> Response:
    await service.delete_holding(portfolio_id, holding_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/app/portfolios/{portfolio_id}/holdings/refresh-current-prices",
    response_model=ApiResponse[HoldingsRefreshStubReadModel],
)
async def refresh_holdings_prices(
    portfolio_id: UUID,
    service: Annotated[GatewayService, Depends(get_gateway_service)],
) -> ApiResponse[HoldingsRefreshStubReadModel]:
    return ApiResponse(data=await service.refresh_holdings_prices(portfolio_id))


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


@router.get("/app/marketdata/instruments/search", response_model=ApiResponse[dict])
async def search_marketdata_instruments(
    service: Annotated[GatewayService, Depends(get_gateway_service)],
    q: str = Query(..., min_length=1),
    limit: int | None = Query(default=None, ge=1, le=25),
) -> ApiResponse[dict]:
    started_at = time.perf_counter()
    LOGGER.info('search_trace gateway_router_enter q="%s" limit=%s', q, limit)
    try:
        payload = await service.search_marketdata_instruments(q=q, limit=limit)
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        LOGGER.info(
            "search_trace gateway_router_exit success=true duration_ms=%s q=%r limit=%s",
            duration_ms,
            q,
            limit,
        )
        return ApiResponse(data=payload)
    except Exception:
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        LOGGER.exception(
            "search_trace gateway_router_exit success=false duration_ms=%s q=%r limit=%s",
            duration_ms,
            q,
            limit,
        )
        raise


@router.get("/app/marketdata/instruments/{symbol}/summary", response_model=ApiResponse[dict])
async def marketdata_summary(
    symbol: str,
    service: Annotated[GatewayService, Depends(get_gateway_service)],
) -> ApiResponse[dict]:
    return ApiResponse(data=await service.get_marketdata_summary(symbol))


@router.get("/app/marketdata/instruments/{symbol}/blocks", response_model=ApiResponse[dict])
async def marketdata_blocks(
    symbol: str,
    service: Annotated[GatewayService, Depends(get_gateway_service)],
) -> ApiResponse[dict]:
    return ApiResponse(data=await service.get_marketdata_blocks(symbol))


@router.get("/app/marketdata/instruments/{symbol}/prices", response_model=ApiResponse[dict])
async def marketdata_prices(
    symbol: str,
    service: Annotated[GatewayService, Depends(get_gateway_service)],
    range_value: str | None = Query(default=None, alias="range"),
    interval: str | None = Query(default=None),
) -> ApiResponse[dict]:
    return ApiResponse(
        data=await service.get_marketdata_prices(symbol, range_value=range_value, interval=interval)
    )


@router.get("/app/marketdata/instruments/{symbol}/history", response_model=ApiResponse[dict])
async def marketdata_history(
    symbol: str,
    service: Annotated[GatewayService, Depends(get_gateway_service)],
    range_value: Literal["1m", "3m", "6m", "ytd", "1y", "max"] | None = Query(default=None, alias="range"),
) -> ApiResponse[dict]:
    return ApiResponse(data=await service.get_marketdata_history(symbol, range_value=range_value))


@router.get("/app/marketdata/instruments/{symbol}/full", response_model=ApiResponse[dict])
async def marketdata_full(
    symbol: str,
    service: Annotated[GatewayService, Depends(get_gateway_service)],
) -> ApiResponse[dict]:
    return ApiResponse(data=await service.get_marketdata_full(symbol))


@router.get("/app/marketdata/instruments/{symbol}/profile", response_model=ApiResponse[MarketdataProfileReadModel])
async def marketdata_profile(
    symbol: str,
    service: Annotated[GatewayService, Depends(get_gateway_service)],
) -> ApiResponse[MarketdataProfileReadModel]:
    return ApiResponse(data=await service.get_marketdata_profile(symbol))


@router.post("/app/marketdata/instruments/{symbol}/refresh-price", response_model=ApiResponse[dict])
async def marketdata_refresh_price(
    symbol: str,
    service: Annotated[GatewayService, Depends(get_gateway_service)],
) -> ApiResponse[dict]:
    return ApiResponse(data=await service.refresh_marketdata_price(symbol))


@router.get("/app/marketdata/instruments/{symbol}/selection", response_model=ApiResponse[MarketdataProfileReadModel])
async def marketdata_selection(
    symbol: str,
    service: Annotated[GatewayService, Depends(get_gateway_service)],
) -> ApiResponse[MarketdataProfileReadModel]:
    return ApiResponse(data=await service.get_marketdata_profile(symbol))


@router.get("/app/marketdata/depot/holdings-summary", response_model=ApiResponse[dict])
async def marketdata_holdings_summary(
    service: Annotated[GatewayService, Depends(get_gateway_service)],
    symbols: str = Query(..., min_length=1),
) -> ApiResponse[dict]:
    return ApiResponse(data=await service.get_marketdata_holdings_summary(symbols))


@router.get("/app/marketdata/batch/prices", response_model=ApiResponse[dict])
async def marketdata_batch_prices(
    service: Annotated[GatewayService, Depends(get_gateway_service)],
    symbols: str = Query(..., min_length=1),
) -> ApiResponse[dict]:
    return ApiResponse(data=await service.get_marketdata_batch_prices(symbols))


@router.get("/app/marketdata/batch/history", response_model=ApiResponse[dict])
async def marketdata_batch_history(
    service: Annotated[GatewayService, Depends(get_gateway_service)],
    symbols: str = Query(..., min_length=1),
    range_value: Literal["1m", "3m", "6m", "ytd", "1y", "max"] = Query(default="3m", alias="range"),
) -> ApiResponse[dict]:
    return ApiResponse(data=await service.get_marketdata_batch_history(symbols, range_value=range_value))


@router.get("/app/marketdata/instruments/{symbol}/snapshot", response_model=ApiResponse[dict])
async def marketdata_snapshot(
    symbol: str,
    service: Annotated[GatewayService, Depends(get_gateway_service)],
) -> ApiResponse[dict]:
    return ApiResponse(data=await service.get_marketdata_snapshot(symbol))


@router.get("/app/marketdata/instruments/{symbol}/fundamentals", response_model=ApiResponse[dict])
async def marketdata_fundamentals(
    symbol: str,
    service: Annotated[GatewayService, Depends(get_gateway_service)],
) -> ApiResponse[dict]:
    return ApiResponse(data=await service.get_marketdata_fundamentals(symbol))


@router.get("/app/marketdata/instruments/{symbol}/metrics", response_model=ApiResponse[dict])
async def marketdata_metrics(
    symbol: str,
    service: Annotated[GatewayService, Depends(get_gateway_service)],
) -> ApiResponse[dict]:
    return ApiResponse(data=await service.get_marketdata_metrics(symbol))


@router.get("/app/marketdata/instruments/{symbol}/financials", response_model=ApiResponse[dict])
async def marketdata_financials(
    symbol: str,
    service: Annotated[GatewayService, Depends(get_gateway_service)],
    period: str | None = Query(default=None),
) -> ApiResponse[dict]:
    return ApiResponse(data=await service.get_marketdata_financials(symbol, period))


@router.get("/app/marketdata/instruments/{symbol}/risk", response_model=ApiResponse[dict])
async def marketdata_risk(
    symbol: str,
    service: Annotated[GatewayService, Depends(get_gateway_service)],
    benchmark: str | None = Query(default=None),
) -> ApiResponse[dict]:
    return ApiResponse(data=await service.get_marketdata_risk(symbol, benchmark))


@router.get("/app/marketdata/instruments/{symbol}/benchmark", response_model=ApiResponse[dict])
async def marketdata_benchmark(
    symbol: str,
    service: Annotated[GatewayService, Depends(get_gateway_service)],
    benchmark: str | None = Query(default=None),
) -> ApiResponse[dict]:
    return ApiResponse(data=await service.get_marketdata_benchmark(symbol, benchmark))


@router.get("/app/marketdata/instruments/{symbol}/timeseries", response_model=ApiResponse[dict])
async def marketdata_timeseries(
    symbol: str,
    service: Annotated[GatewayService, Depends(get_gateway_service)],
    series: str | None = Query(default=None),
    benchmark: str | None = Query(default=None),
) -> ApiResponse[dict]:
    return ApiResponse(data=await service.get_marketdata_timeseries(symbol, series, benchmark))


@router.get("/app/marketdata/instruments/{symbol}/comparison-timeseries", response_model=ApiResponse[dict])
async def marketdata_comparison_timeseries(
    symbol: str,
    service: Annotated[GatewayService, Depends(get_gateway_service)],
    symbols: str = Query(..., min_length=1),
) -> ApiResponse[dict]:
    return ApiResponse(data=await service.get_marketdata_comparison_timeseries(symbol, symbols))


@router.get("/app/marketdata/benchmark-catalog", response_model=ApiResponse[dict])
async def marketdata_benchmark_catalog(
    service: Annotated[GatewayService, Depends(get_gateway_service)],
) -> ApiResponse[dict]:
    return ApiResponse(data=await service.get_marketdata_benchmark_catalog())


@router.get("/app/marketdata/benchmark-search", response_model=ApiResponse[dict])
async def marketdata_benchmark_search(
    service: Annotated[GatewayService, Depends(get_gateway_service)],
    q: str = Query(..., min_length=1),
) -> ApiResponse[dict]:
    return ApiResponse(data=await service.search_marketdata_benchmark(q))
