from __future__ import annotations

import asyncio
import logging
import time
from uuid import UUID

import httpx
from fastapi import HTTPException, status

from app.circuit_breaker import CircuitBreaker, CircuitOpenError
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
    HealthDependency,
    HoldingCreatePayload,
    HoldingsRefreshStubReadModel,
    HoldingReadModel,
    HoldingUpdatePayload,
    PersonBankAssignmentReadModel,
    PersonCreatePayload,
    PersonDetailReadModel,
    PersonListReadModel,
    PersonReadModel,
    PersonUpdatePayload,
    PortfolioCreatePayload,
    PortfolioAttributionReadModel,
    PortfolioDataCoverageReadModel,
    PortfolioContributorsReadModel,
    PortfolioDashboardReadModel,
    PortfolioExposuresReadModel,
    PortfolioHoldingsReadModel,
    PortfolioPerformanceReadModel,
    PortfolioRiskReadModel,
    PortfolioDetailReadModel,
    PortfolioListReadModel,
    PortfolioReadModel,
    PortfolioSummaryReadModel,
    TaxAllowanceReadModel,
)

LOGGER = logging.getLogger(__name__)


class GatewayService:
    """
    BFF service layer.

    5.1  — One long-lived AsyncClient is shared across all requests.
           httpx maintains per-host connection pools internally, so we get
           TCP-connection reuse for all six upstream services without managing
           six separate clients.

    5.3  — One CircuitBreaker per upstream service.  When a service accumulates
           failure_threshold consecutive errors the breaker opens and subsequent
           calls are rejected immediately with 503 instead of waiting for the
           full timeout.  After recovery_timeout_seconds one probe is allowed
           through; on success the breaker resets.

    5.4  — Dashboard section fetches are issued in parallel via asyncio.gather.
    """

    def __init__(
        self,
        analytics_base_url: str,
        person_base_url: str,
        masterdata_base_url: str,
        account_base_url: str,
        portfolio_base_url: str,
        marketdata_base_url: str,
        timeout_seconds: float,
        circuit_breaker_failure_threshold: int = 5,
        circuit_breaker_recovery_timeout_seconds: float = 30.0,
    ) -> None:
        self._analytics_base_url = analytics_base_url.rstrip("/")
        self._person_base_url = person_base_url.rstrip("/")
        self._masterdata_base_url = masterdata_base_url.rstrip("/")
        self._account_base_url = account_base_url.rstrip("/")
        self._portfolio_base_url = portfolio_base_url.rstrip("/")
        self._marketdata_base_url = marketdata_base_url.rstrip("/")
        self._timeout = timeout_seconds

        # 5.1: single pooled client for all upstream requests
        self._client = httpx.AsyncClient(
            timeout=self._timeout,
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
        )

        # 5.3: per-service circuit breakers
        self._circuit_breakers: dict[str, CircuitBreaker] = {
            self._analytics_base_url: CircuitBreaker(
                "analytics-service",
                failure_threshold=circuit_breaker_failure_threshold,
                recovery_timeout_seconds=circuit_breaker_recovery_timeout_seconds,
            ),
            self._person_base_url: CircuitBreaker(
                "person-service",
                failure_threshold=circuit_breaker_failure_threshold,
                recovery_timeout_seconds=circuit_breaker_recovery_timeout_seconds,
            ),
            self._masterdata_base_url: CircuitBreaker(
                "masterdata-service",
                failure_threshold=circuit_breaker_failure_threshold,
                recovery_timeout_seconds=circuit_breaker_recovery_timeout_seconds,
            ),
            self._account_base_url: CircuitBreaker(
                "account-service",
                failure_threshold=circuit_breaker_failure_threshold,
                recovery_timeout_seconds=circuit_breaker_recovery_timeout_seconds,
            ),
            self._portfolio_base_url: CircuitBreaker(
                "portfolio-service",
                failure_threshold=circuit_breaker_failure_threshold,
                recovery_timeout_seconds=circuit_breaker_recovery_timeout_seconds,
            ),
            self._marketdata_base_url: CircuitBreaker(
                "marketdata-service",
                failure_threshold=circuit_breaker_failure_threshold,
                recovery_timeout_seconds=circuit_breaker_recovery_timeout_seconds,
            ),
        }

    async def aclose(self) -> None:
        """Release the shared connection pool.  Called on application shutdown."""
        await self._client.aclose()

    def _get_circuit_breaker(self, url: str) -> CircuitBreaker | None:
        for base_url, cb in self._circuit_breakers.items():
            if url.startswith(base_url):
                return cb
        return None

    # ------------------------------------------------------------------
    # Persons
    # ------------------------------------------------------------------

    async def list_persons(self, **kwargs) -> PersonListReadModel:
        payload = await self._request_person_service("GET", "/api/v1/persons", params=kwargs)
        return PersonListReadModel.model_validate(payload)

    async def create_person(self, person: PersonCreatePayload) -> PersonReadModel:
        return PersonReadModel.model_validate(
            await self._request_person_service("POST", "/api/v1/persons", json=person.model_dump())
        )

    async def get_person(self, person_id: UUID) -> PersonDetailReadModel:
        return PersonDetailReadModel.model_validate(
            await self._request_person_service("GET", f"/api/v1/persons/{person_id}")
        )

    async def update_person(self, person_id: UUID, person: PersonUpdatePayload) -> PersonReadModel:
        payload = await self._request_person_service(
            "PATCH", f"/api/v1/persons/{person_id}", json=person.model_dump(exclude_none=True)
        )
        return PersonReadModel.model_validate(payload)

    async def delete_person(self, person_id: UUID) -> None:
        await self._request_person_service(
            "DELETE", f"/api/v1/persons/{person_id}", expect_no_content=True
        )

    async def list_person_banks(self, person_id: UUID) -> AssignmentListReadModel:
        return AssignmentListReadModel.model_validate(
            await self._request_person_service("GET", f"/api/v1/persons/{person_id}/banks")
        )

    async def assign_bank(self, person_id: UUID, bank_id: UUID) -> PersonBankAssignmentReadModel:
        return PersonBankAssignmentReadModel.model_validate(
            await self._request_person_service(
                "POST", f"/api/v1/persons/{person_id}/banks/{bank_id}"
            )
        )

    async def unassign_bank(self, person_id: UUID, bank_id: UUID) -> None:
        await self._request_person_service(
            "DELETE", f"/api/v1/persons/{person_id}/banks/{bank_id}", expect_no_content=True
        )

    async def list_allowances(self, person_id: UUID, tax_year: int | None = None) -> AllowanceListReadModel:
        payload = await self._request_person_service(
            "GET", f"/api/v1/persons/{person_id}/allowances", params={"tax_year": tax_year}
        )
        return AllowanceListReadModel.model_validate(payload)

    async def set_allowance(
        self, person_id: UUID, bank_id: UUID, payload: AllowanceUpsertPayload
    ) -> TaxAllowanceReadModel:
        result = await self._request_person_service(
            "PUT", f"/api/v1/persons/{person_id}/allowances/{bank_id}", json=payload.model_dump()
        )
        return TaxAllowanceReadModel.model_validate(result)

    async def allowance_summary(self, person_id: UUID, tax_year: int) -> AllowanceSummaryReadModel:
        payload = await self._request_person_service(
            "GET",
            f"/api/v1/persons/{person_id}/allowances/summary",
            params={"tax_year": tax_year},
        )
        return AllowanceSummaryReadModel.model_validate(payload)

    # ------------------------------------------------------------------
    # Banks (masterdata)
    # ------------------------------------------------------------------

    async def list_banks(self) -> BankListReadModel:
        return BankListReadModel.model_validate(
            await self._request_masterdata_service("GET", "/api/v1/banks")
        )

    async def create_bank(self, bank: BankCreatePayload) -> BankReadModel:
        return BankReadModel.model_validate(
            await self._request_masterdata_service("POST", "/api/v1/banks", json=bank.model_dump())
        )

    # ------------------------------------------------------------------
    # Accounts
    # ------------------------------------------------------------------

    async def list_accounts(self, person_id: UUID) -> list[AccountReadModel]:
        payload = await self._request_account_service(
            "GET", f"/api/v1/persons/{person_id}/accounts"
        )
        return [AccountReadModel.model_validate(item) for item in payload]

    async def get_account(self, person_id: UUID, account_id: UUID) -> AccountReadModel:
        payload = await self._request_account_service(
            "GET", f"/api/v1/persons/{person_id}/accounts/{account_id}"
        )
        return AccountReadModel.model_validate(payload)

    async def create_account(self, person_id: UUID, payload: AccountCreatePayload) -> AccountReadModel:
        data = await self._request_account_service(
            "POST",
            f"/api/v1/persons/{person_id}/accounts",
            json=payload.model_dump(mode="json", exclude_none=True),
        )
        return AccountReadModel.model_validate(data)

    async def update_account(
        self, person_id: UUID, account_id: UUID, payload: AccountUpdatePayload
    ) -> AccountReadModel:
        data = await self._request_account_service(
            "PATCH",
            f"/api/v1/persons/{person_id}/accounts/{account_id}",
            json=payload.model_dump(mode="json", exclude_none=True),
        )
        return AccountReadModel.model_validate(data)

    async def delete_account(self, person_id: UUID, account_id: UUID) -> None:
        await self._request_account_service(
            "DELETE",
            f"/api/v1/persons/{person_id}/accounts/{account_id}",
            expect_no_content=True,
        )

    # ------------------------------------------------------------------
    # Portfolios
    # ------------------------------------------------------------------

    async def list_portfolios(self, person_id: UUID) -> PortfolioListReadModel:
        data = await self._request_portfolio_service(
            "GET", f"/api/v1/persons/{person_id}/portfolios"
        )
        return PortfolioListReadModel.model_validate(data)

    async def create_portfolio(self, person_id: UUID, payload: PortfolioCreatePayload) -> PortfolioReadModel:
        data = await self._request_portfolio_service(
            "POST",
            "/api/v1/portfolios",
            json={"person_id": str(person_id), **payload.model_dump()},
        )
        return PortfolioReadModel.model_validate(data)

    async def get_portfolio(self, portfolio_id: UUID) -> PortfolioDetailReadModel:
        return PortfolioDetailReadModel.model_validate(
            await self._request_portfolio_service("GET", f"/api/v1/portfolios/{portfolio_id}")
        )

    async def create_holding(self, portfolio_id: UUID, payload: HoldingCreatePayload) -> HoldingReadModel:
        data = await self._request_portfolio_service(
            "POST",
            f"/api/v1/portfolios/{portfolio_id}/holdings",
            json=payload.model_dump(exclude_none=True),
        )
        return HoldingReadModel.model_validate(data)

    async def update_holding(
        self, portfolio_id: UUID, holding_id: UUID, payload: HoldingUpdatePayload
    ) -> HoldingReadModel:
        data = await self._request_portfolio_service(
            "PATCH",
            f"/api/v1/portfolios/{portfolio_id}/holdings/{holding_id}",
            json=payload.model_dump(exclude_none=True),
        )
        return HoldingReadModel.model_validate(data)

    async def delete_holding(self, portfolio_id: UUID, holding_id: UUID) -> None:
        await self._request_portfolio_service(
            "DELETE",
            f"/api/v1/portfolios/{portfolio_id}/holdings/{holding_id}",
            expect_no_content=True,
        )

    async def refresh_holdings_prices(self, portfolio_id: UUID) -> HoldingsRefreshStubReadModel:
        data = await self._request_portfolio_service(
            "POST", f"/api/v1/portfolios/{portfolio_id}/holdings/refresh-current-prices"
        )
        return HoldingsRefreshStubReadModel.model_validate(data)

    async def get_depot_portfolio(self, person_id: UUID, account_id: UUID) -> PortfolioReadModel:
        account = await self.get_account(person_id, account_id)
        if account.account_type != "depot":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Portfolio-Zuordnung ist nur fuer Depotkonten verfuegbar",
            )

        if account.portfolio_id is not None:
            portfolio = PortfolioReadModel.model_validate(
                await self._request_portfolio_service(
                    "GET", f"/api/v1/portfolios/{account.portfolio_id}"
                )
            )
            if portfolio.person_id != person_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Depotkonto verweist auf ein Portfolio einer anderen Person",
                )
            return portfolio

        portfolio = await self.create_portfolio(
            person_id,
            PortfolioCreatePayload(display_name=account.label),
        )
        await self.update_account(
            person_id,
            account_id,
            AccountUpdatePayload(portfolio_id=portfolio.portfolio_id),
        )
        return portfolio

    # ------------------------------------------------------------------
    # Marketdata
    # ------------------------------------------------------------------

    async def search_marketdata_instruments(self, *, q: str, limit: int | None = None) -> dict:
        started_at = time.perf_counter()
        LOGGER.info('search_trace gateway_service_before_upstream q="%s" limit=%s', q, limit)
        try:
            payload = await self._request_marketdata_service(
                "GET",
                "/api/v1/marketdata/instruments/search",
                params={"q": q, "limit": limit},
            )
            duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
            LOGGER.info(
                "search_trace gateway_service_after_upstream success=true duration_ms=%s q=%r limit=%s",
                duration_ms, q, limit,
            )
            return payload
        except Exception as exc:
            duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
            status_code = getattr(exc, "status_code", None)
            if isinstance(exc, HTTPException):
                status_code = exc.status_code
            LOGGER.exception(
                "search_trace gateway_service_upstream_error success=false duration_ms=%s q=%r "
                "limit=%s status_code=%s exc_type=%s",
                duration_ms, q, limit, status_code, type(exc).__name__,
            )
            raise

    async def get_marketdata_summary(self, symbol: str) -> dict:
        return await self._request_marketdata_service(
            "GET", f"/api/v1/marketdata/instruments/{symbol}/summary"
        )

    async def get_marketdata_blocks(self, symbol: str) -> dict:
        return await self._request_marketdata_service(
            "GET", f"/api/v1/marketdata/instruments/{symbol}/blocks"
        )

    async def get_marketdata_prices(
        self, symbol: str, *, range_value: str | None = None, interval: str | None = None
    ) -> dict:
        return await self._request_marketdata_service(
            "GET",
            f"/api/v1/marketdata/instruments/{symbol}/prices",
            params={"range": range_value, "interval": interval},
        )

    async def get_marketdata_history(self, symbol: str, *, range_value: str | None = None) -> dict:
        return await self._request_marketdata_service(
            "GET",
            f"/api/v1/marketdata/instruments/{symbol}/history",
            params={"range": range_value},
        )

    async def get_marketdata_full(self, symbol: str) -> dict:
        return await self._request_marketdata_service(
            "GET", f"/api/v1/marketdata/instruments/{symbol}/full"
        )

    async def get_marketdata_profile(self, symbol: str) -> dict:
        return await self._request_marketdata_service(
            "GET", f"/api/v1/marketdata/instruments/{symbol}/profile"
        )

    async def get_marketdata_holdings_summary(self, symbols: str) -> dict:
        return await self._request_marketdata_service(
            "GET", "/api/v1/marketdata/depot/holdings-summary", params={"symbols": symbols}
        )

    async def get_marketdata_batch_prices(self, symbols: str) -> dict:
        return await self._request_marketdata_service(
            "GET", "/api/v1/marketdata/batch/prices", params={"symbols": symbols}
        )

    async def get_marketdata_batch_history(self, symbols: str, *, range_value: str | None = None) -> dict:
        return await self._request_marketdata_service(
            "GET",
            "/api/v1/marketdata/batch/history",
            params={"symbols": symbols, "range": range_value},
        )

    async def get_marketdata_snapshot(self, symbol: str) -> dict:
        return await self._request_marketdata_service(
            "GET", f"/api/v1/marketdata/instruments/{symbol}/snapshot"
        )

    async def get_marketdata_fundamentals(self, symbol: str) -> dict:
        return await self._request_marketdata_service(
            "GET", f"/api/v1/marketdata/instruments/{symbol}/fundamentals"
        )

    async def get_marketdata_metrics(self, symbol: str) -> dict:
        return await self._request_marketdata_service(
            "GET", f"/api/v1/marketdata/instruments/{symbol}/metrics"
        )

    async def get_marketdata_financials(self, symbol: str, period: str | None = None) -> dict:
        return await self._request_marketdata_service(
            "GET",
            f"/api/v1/marketdata/instruments/{symbol}/financials",
            params={"period": period},
        )

    async def get_marketdata_risk(self, symbol: str, benchmark: str | None = None) -> dict:
        return await self._request_marketdata_service(
            "GET",
            f"/api/v1/marketdata/instruments/{symbol}/risk",
            params={"benchmark": benchmark},
        )

    async def get_marketdata_benchmark(self, symbol: str, benchmark: str | None = None) -> dict:
        return await self._request_marketdata_service(
            "GET",
            f"/api/v1/marketdata/instruments/{symbol}/benchmark",
            params={"benchmark": benchmark},
        )

    async def get_marketdata_timeseries(
        self, symbol: str, series: str | None = None, benchmark: str | None = None
    ) -> dict:
        return await self._request_marketdata_service(
            "GET",
            f"/api/v1/marketdata/instruments/{symbol}/timeseries",
            params={"series": series, "benchmark": benchmark},
        )

    async def get_marketdata_comparison_timeseries(self, symbol: str, symbols: str) -> dict:
        return await self._request_marketdata_service(
            "GET",
            f"/api/v1/marketdata/instruments/{symbol}/comparison-timeseries",
            params={"symbols": symbols},
        )

    async def get_marketdata_benchmark_catalog(self) -> dict:
        return await self._request_marketdata_service(
            "GET", "/api/v1/marketdata/benchmark-catalog"
        )

    async def search_marketdata_benchmark(self, query: str) -> dict:
        return await self._request_marketdata_service(
            "GET", "/api/v1/marketdata/benchmark-search", params={"q": query}
        )

    async def refresh_marketdata_price(self, symbol: str) -> dict:
        return await self._request_marketdata_service(
            "POST", f"/api/v1/marketdata/instruments/{symbol}/refresh-price"
        )

    # Deprecated: kept for backwards compatibility with older frontend clients.
    async def get_marketdata_selection(self, symbol: str) -> dict:
        return await self.get_marketdata_profile(symbol)

    # ------------------------------------------------------------------
    # Analytics
    # ------------------------------------------------------------------

    async def get_analytics_overview(self, person_id: UUID) -> dict:
        return await self._get_analytics_payload(person_id, "overview")

    async def get_portfolio_summary(self, person_id: UUID) -> PortfolioSummaryReadModel:
        payload = await self._request_json(
            f"{self._analytics_base_url}/api/v1/analytics/persons/{person_id}/portfolio-summary",
            "GET",
        )
        return PortfolioSummaryReadModel.model_validate(payload)

    async def get_portfolio_dashboard(
        self, person_id: UUID, range_value: str = "3m"
    ) -> PortfolioDashboardReadModel:
        payload = await self._request_json(
            f"{self._analytics_base_url}/api/v1/analytics/persons/{person_id}/portfolio-dashboard",
            "GET",
            params={"range": range_value},
        )
        return PortfolioDashboardReadModel.model_validate(payload)

    async def get_portfolio_performance(self, person_id: UUID) -> PortfolioPerformanceReadModel:
        payload = await self._request_json(
            f"{self._analytics_base_url}/api/v1/analytics/persons/{person_id}/portfolio-performance",
            "GET",
        )
        return PortfolioPerformanceReadModel.model_validate(payload)

    async def get_portfolio_exposures(self, person_id: UUID) -> PortfolioExposuresReadModel:
        payload = await self._request_json(
            f"{self._analytics_base_url}/api/v1/analytics/persons/{person_id}/portfolio-exposures",
            "GET",
        )
        return PortfolioExposuresReadModel.model_validate(payload)

    async def get_portfolio_holdings(self, person_id: UUID) -> PortfolioHoldingsReadModel:
        payload = await self._request_json(
            f"{self._analytics_base_url}/api/v1/analytics/persons/{person_id}/portfolio-holdings",
            "GET",
        )
        return PortfolioHoldingsReadModel.model_validate(payload)

    async def get_portfolio_risk(self, person_id: UUID) -> PortfolioRiskReadModel:
        payload = await self._request_json(
            f"{self._analytics_base_url}/api/v1/analytics/persons/{person_id}/portfolio-risk",
            "GET",
        )
        return PortfolioRiskReadModel.model_validate(payload)

    async def get_portfolio_contributors(
        self, person_id: UUID, range_value: str = "3m"
    ) -> PortfolioContributorsReadModel:
        payload = await self._request_json(
            f"{self._analytics_base_url}/api/v1/analytics/persons/{person_id}/portfolio-contributors",
            "GET",
            params={"range": range_value},
        )
        return PortfolioContributorsReadModel.model_validate(payload)

    async def get_portfolio_attribution(
        self, person_id: UUID, range_value: str = "3m"
    ) -> PortfolioAttributionReadModel:
        payload = await self._request_json(
            f"{self._analytics_base_url}/api/v1/analytics/persons/{person_id}/portfolio-attribution",
            "GET",
            params={"range": range_value},
        )
        return PortfolioAttributionReadModel.model_validate(payload)

    async def get_portfolio_data_coverage(self, person_id: UUID) -> PortfolioDataCoverageReadModel:
        payload = await self._request_json(
            f"{self._analytics_base_url}/api/v1/analytics/persons/{person_id}/portfolio-data-coverage",
            "GET",
        )
        return PortfolioDataCoverageReadModel.model_validate(payload)

    async def get_dashboard_section(self, person_id: UUID, section: str) -> dict:
        response = await self._raw_get(
            f"{self._analytics_base_url}/api/v1/analytics/persons/{person_id}/dashboard/{section}"
        )
        response.raise_for_status()
        return response.json()["data"]

    async def get_dashboard(self, person_id: UUID) -> DashboardReadModel:
        # 5.4: fetch all four sections concurrently
        overview_section, allocation_section, metrics_section, timeseries_section = (
            await asyncio.gather(
                self.get_dashboard_section(person_id, "overview"),
                self.get_dashboard_section(person_id, "allocation"),
                self.get_dashboard_section(person_id, "metrics"),
                self.get_dashboard_section(person_id, "timeseries"),
            )
        )
        overview = overview_section.get("payload", {})
        overview["_state"] = overview_section.get("state")
        return DashboardReadModel(
            person_id=person_id,
            overview=overview,
            allocation={**allocation_section.get("payload", {}), "_state": allocation_section.get("state")},
            metrics={**metrics_section.get("payload", {}), "_state": metrics_section.get("state")},
            timeseries={**timeseries_section.get("payload", {}), "_state": timeseries_section.get("state")},
            kpis=overview.get("kpis", []),
        )

    async def dependency_health(self, person_id: UUID) -> GatewayHealthReadModel:
        # probe all services in parallel
        results = await asyncio.gather(
            self._health_probe("analytics-service", f"{self._analytics_base_url}/health"),
            self._health_probe("person-service", f"{self._person_base_url}/health"),
            self._health_probe("account-service", f"{self._account_base_url}/health"),
            self._health_probe("portfolio-service", f"{self._portfolio_base_url}/health"),
            self._health_probe("marketdata-service", f"{self._marketdata_base_url}/health"),
        )
        status = "up" if all(dep.status == "up" for dep in results) else "degraded"
        return GatewayHealthReadModel(status=status, dependencies=list(results))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _request_person_service(self, method: str, path: str, **kwargs) -> dict:
        return await self._request_json(f"{self._person_base_url}{path}", method, **kwargs)

    async def _request_masterdata_service(self, method: str, path: str, **kwargs) -> dict:
        return await self._request_json(
            f"{self._masterdata_base_url}{path}", method, error_label="Masterdata-Service", **kwargs
        )

    async def _request_account_service(self, method: str, path: str, **kwargs) -> dict | list[dict]:
        return await self._request_json(f"{self._account_base_url}{path}", method, **kwargs)

    async def _request_portfolio_service(self, method: str, path: str, **kwargs) -> dict:
        return await self._request_json(
            f"{self._portfolio_base_url}{path}", method, error_label="Portfolio-Service", **kwargs
        )

    async def _request_marketdata_service(self, method: str, path: str, **kwargs) -> dict:
        return await self._request_json(
            f"{self._marketdata_base_url}{path}", method, error_label="Marketdata-Service", **kwargs
        )

    async def _raw_get(self, url: str) -> httpx.Response:
        """Issue a GET using the shared client without JSON unwrapping."""
        cb = self._get_circuit_breaker(url)
        if cb:
            try:
                cb.before_call()
            except CircuitOpenError as exc:
                raise HTTPException(
                    status_code=503,
                    detail=f"{exc.service_name} temporarily unavailable (circuit open)",
                ) from exc
        try:
            response = await self._client.get(url)
            if cb:
                cb.record_success()
            return response
        except (httpx.RequestError, httpx.TimeoutException):
            if cb:
                cb.record_failure()
            raise

    async def _request_json(
        self,
        url: str,
        method: str,
        *,
        json: dict | None = None,
        params: dict | None = None,
        expect_no_content: bool = False,
        error_label: str | None = None,
    ) -> dict | list[dict]:
        query = {k: v for k, v in (params or {}).items() if v is not None}

        # 5.3: circuit breaker check
        cb = self._get_circuit_breaker(url)
        if cb:
            try:
                cb.before_call()
            except CircuitOpenError as exc:
                raise HTTPException(
                    status_code=503,
                    detail=f"{exc.service_name} temporarily unavailable (circuit open)",
                ) from exc

        try:
            response = await self._client.request(method, url, json=json, params=query)
            if cb:
                cb.record_success()
        except httpx.RequestError as exc:
            if cb:
                cb.record_failure()
            if error_label:
                raise HTTPException(
                    status_code=502,
                    detail=f"{error_label} ist derzeit nicht erreichbar. Bitte später erneut versuchen.",
                ) from exc
            raise
        except httpx.TimeoutException as exc:
            if cb:
                cb.record_failure()
            label = error_label or "Upstream-Service"
            raise HTTPException(
                status_code=504,
                detail=f"{label} hat nicht rechtzeitig geantwortet.",
            ) from exc

        if response.status_code >= 400:
            # 4xx are client errors — don't penalise the circuit
            raise HTTPException(
                status_code=response.status_code, detail=self._error_detail(response)
            )
        if expect_no_content:
            return {}
        return response.json()["data"]

    @staticmethod
    def _error_detail(response: httpx.Response) -> object:
        try:
            data = response.json()
            return data.get("detail", data) if isinstance(data, dict) else data
        except Exception:
            return response.text

    async def _get_analytics_payload(self, person_id: UUID, endpoint: str) -> dict:
        response = await self._raw_get(
            f"{self._analytics_base_url}/api/v1/analytics/persons/{person_id}/{endpoint}"
        )
        response.raise_for_status()
        return response.json()["data"]

    async def _health_probe(self, service: str, url: str) -> HealthDependency:
        try:
            response = await self._client.get(url)
            return HealthDependency(
                service=service,
                status="up" if response.status_code == 200 else "down",
                detail=None if response.status_code == 200 else f"HTTP {response.status_code}",
            )
        except Exception as exc:
            return HealthDependency(service=service, status="down", detail=str(exc))
