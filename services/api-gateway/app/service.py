from __future__ import annotations

from uuid import UUID

import httpx
from fastapi import HTTPException

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
    HoldingReadModel,
    HoldingUpdatePayload,
    PersonBankAssignmentReadModel,
    PersonCreatePayload,
    PersonDetailReadModel,
    PersonListReadModel,
    PersonReadModel,
    PersonUpdatePayload,
    PortfolioCreatePayload,
    PortfolioDetailReadModel,
    PortfolioListReadModel,
    PortfolioReadModel,
    TaxAllowanceReadModel,
)


class GatewayService:
    def __init__(
        self,
        analytics_base_url: str,
        person_base_url: str,
        masterdata_base_url: str,
        account_base_url: str,
        portfolio_base_url: str,
        marketdata_base_url: str,
        timeout_seconds: float,
    ) -> None:
        self._analytics_base_url = analytics_base_url.rstrip("/")
        self._person_base_url = person_base_url.rstrip("/")
        self._masterdata_base_url = masterdata_base_url.rstrip("/")
        self._account_base_url = account_base_url.rstrip("/")
        self._portfolio_base_url = portfolio_base_url.rstrip("/")
        self._marketdata_base_url = marketdata_base_url.rstrip("/")
        self._timeout = timeout_seconds

    async def list_persons(self, **kwargs) -> PersonListReadModel:
        payload = await self._request_person_service("GET", "/api/v1/persons", params=kwargs)
        return PersonListReadModel.model_validate(payload)

    async def create_person(self, person: PersonCreatePayload) -> PersonReadModel:
        return PersonReadModel.model_validate(
            await self._request_person_service("POST", "/api/v1/persons", json=person.model_dump())
        )

    async def get_person(self, person_id: UUID) -> PersonDetailReadModel:
        return PersonDetailReadModel.model_validate(await self._request_person_service("GET", f"/api/v1/persons/{person_id}"))

    async def update_person(self, person_id: UUID, person: PersonUpdatePayload) -> PersonReadModel:
        payload = await self._request_person_service("PATCH", f"/api/v1/persons/{person_id}", json=person.model_dump(exclude_none=True))
        return PersonReadModel.model_validate(payload)

    async def delete_person(self, person_id: UUID) -> None:
        await self._request_person_service("DELETE", f"/api/v1/persons/{person_id}", expect_no_content=True)

    async def list_person_banks(self, person_id: UUID) -> AssignmentListReadModel:
        return AssignmentListReadModel.model_validate(await self._request_person_service("GET", f"/api/v1/persons/{person_id}/banks"))

    async def assign_bank(self, person_id: UUID, bank_id: UUID) -> PersonBankAssignmentReadModel:
        return PersonBankAssignmentReadModel.model_validate(await self._request_person_service("POST", f"/api/v1/persons/{person_id}/banks/{bank_id}"))

    async def unassign_bank(self, person_id: UUID, bank_id: UUID) -> None:
        await self._request_person_service("DELETE", f"/api/v1/persons/{person_id}/banks/{bank_id}", expect_no_content=True)

    async def list_allowances(self, person_id: UUID, tax_year: int | None = None) -> AllowanceListReadModel:
        payload = await self._request_person_service("GET", f"/api/v1/persons/{person_id}/allowances", params={"tax_year": tax_year})
        return AllowanceListReadModel.model_validate(payload)

    async def set_allowance(self, person_id: UUID, bank_id: UUID, payload: AllowanceUpsertPayload) -> TaxAllowanceReadModel:
        result = await self._request_person_service("PUT", f"/api/v1/persons/{person_id}/allowances/{bank_id}", json=payload.model_dump())
        return TaxAllowanceReadModel.model_validate(result)

    async def allowance_summary(self, person_id: UUID, tax_year: int) -> AllowanceSummaryReadModel:
        payload = await self._request_person_service("GET", f"/api/v1/persons/{person_id}/allowances/summary", params={"tax_year": tax_year})
        return AllowanceSummaryReadModel.model_validate(payload)

    async def list_banks(self) -> BankListReadModel:
        return BankListReadModel.model_validate(await self._request_masterdata_service("GET", "/api/v1/banks"))

    async def create_bank(self, bank: BankCreatePayload) -> BankReadModel:
        return BankReadModel.model_validate(await self._request_masterdata_service("POST", "/api/v1/banks", json=bank.model_dump()))

    async def list_accounts(self, person_id: UUID) -> list[AccountReadModel]:
        payload = await self._request_account_service("GET", f"/api/v1/persons/{person_id}/accounts")
        return [AccountReadModel.model_validate(item) for item in payload]

    async def get_account(self, person_id: UUID, account_id: UUID) -> AccountReadModel:
        payload = await self._request_account_service("GET", f"/api/v1/persons/{person_id}/accounts/{account_id}")
        return AccountReadModel.model_validate(payload)

    async def create_account(self, person_id: UUID, payload: AccountCreatePayload) -> AccountReadModel:
        data = await self._request_account_service("POST", f"/api/v1/persons/{person_id}/accounts", json=payload.model_dump(mode="json", exclude_none=True))
        return AccountReadModel.model_validate(data)

    async def update_account(self, person_id: UUID, account_id: UUID, payload: AccountUpdatePayload) -> AccountReadModel:
        data = await self._request_account_service("PATCH", f"/api/v1/persons/{person_id}/accounts/{account_id}", json=payload.model_dump(mode="json", exclude_none=True))
        return AccountReadModel.model_validate(data)

    async def delete_account(self, person_id: UUID, account_id: UUID) -> None:
        await self._request_account_service("DELETE", f"/api/v1/persons/{person_id}/accounts/{account_id}", expect_no_content=True)

    async def list_portfolios(self, person_id: UUID) -> PortfolioListReadModel:
        data = await self._request_portfolio_service("GET", f"/api/v1/persons/{person_id}/portfolios")
        return PortfolioListReadModel.model_validate(data)

    async def create_portfolio(self, person_id: UUID, payload: PortfolioCreatePayload) -> PortfolioReadModel:
        data = await self._request_portfolio_service("POST", "/api/v1/portfolios", json={"person_id": str(person_id), **payload.model_dump()})
        return PortfolioReadModel.model_validate(data)

    async def get_portfolio(self, portfolio_id: UUID) -> PortfolioDetailReadModel:
        return PortfolioDetailReadModel.model_validate(await self._request_portfolio_service("GET", f"/api/v1/portfolios/{portfolio_id}"))

    async def create_holding(self, portfolio_id: UUID, payload: HoldingCreatePayload) -> HoldingReadModel:
        data = await self._request_portfolio_service("POST", f"/api/v1/portfolios/{portfolio_id}/holdings", json=payload.model_dump(exclude_none=True))
        return HoldingReadModel.model_validate(data)

    async def update_holding(self, portfolio_id: UUID, holding_id: UUID, payload: HoldingUpdatePayload) -> HoldingReadModel:
        data = await self._request_portfolio_service("PATCH", f"/api/v1/portfolios/{portfolio_id}/holdings/{holding_id}", json=payload.model_dump(exclude_none=True))
        return HoldingReadModel.model_validate(data)

    async def delete_holding(self, portfolio_id: UUID, holding_id: UUID) -> None:
        await self._request_portfolio_service("DELETE", f"/api/v1/portfolios/{portfolio_id}/holdings/{holding_id}", expect_no_content=True)

    async def search_marketdata_instruments(self, *, q: str, limit: int | None = None) -> dict:
        return await self._request_marketdata_service("GET", "/api/v1/marketdata/instruments/search", params={"q": q, "limit": limit})

    async def get_marketdata_summary(self, symbol: str) -> dict:
        return await self._request_marketdata_service("GET", f"/api/v1/marketdata/instruments/{symbol}/summary")

    async def get_marketdata_blocks(self, symbol: str) -> dict:
        return await self._request_marketdata_service("GET", f"/api/v1/marketdata/instruments/{symbol}/blocks")

    async def get_marketdata_prices(self, symbol: str, *, range_value: str | None = None, interval: str | None = None) -> dict:
        return await self._request_marketdata_service("GET", f"/api/v1/marketdata/instruments/{symbol}/prices", params={"range": range_value, "interval": interval})

    async def get_marketdata_full(self, symbol: str) -> dict:
        return await self._request_marketdata_service("GET", f"/api/v1/marketdata/instruments/{symbol}/full")

    async def get_marketdata_selection(self, symbol: str) -> dict:
        return await self._request_marketdata_service("GET", f"/api/v1/marketdata/instruments/{symbol}/selection")

    async def get_analytics_overview(self, person_id: UUID) -> dict:
        return await self._get_analytics_payload(person_id, "overview")

    async def get_dashboard(self, person_id: UUID) -> DashboardReadModel:
        overview = await self._get_analytics_payload(person_id, "overview")
        return DashboardReadModel(
            person_id=person_id,
            overview=overview,
            allocation=await self._get_analytics_payload(person_id, "allocation"),
            metrics=await self._get_analytics_payload(person_id, "metrics"),
            timeseries=await self._get_analytics_payload(person_id, "timeseries"),
            kpis=overview.get("kpis", []),
        )

    async def dependency_health(self, person_id: UUID) -> GatewayHealthReadModel:
        dependencies = [
            await self._health_probe("analytics-service", f"{self._analytics_base_url}/health"),
            await self._health_probe("person-service", f"{self._person_base_url}/health"),
            await self._health_probe("account-service", f"{self._account_base_url}/health"),
            await self._health_probe("portfolio-service", f"{self._portfolio_base_url}/health"),
            await self._health_probe("marketdata-service", f"{self._marketdata_base_url}/health"),
        ]
        status = "up" if all(dep.status == "up" for dep in dependencies) else "degraded"
        return GatewayHealthReadModel(status=status, dependencies=dependencies)

    async def _request_person_service(self, method: str, path: str, **kwargs) -> dict:
        return await self._request_json(f"{self._person_base_url}{path}", method, **kwargs)

    async def _request_masterdata_service(self, method: str, path: str, **kwargs) -> dict:
        return await self._request_json(f"{self._masterdata_base_url}{path}", method, error_label="Masterdata-Service", **kwargs)

    async def _request_account_service(self, method: str, path: str, **kwargs) -> dict | list[dict]:
        return await self._request_json(f"{self._account_base_url}{path}", method, **kwargs)

    async def _request_portfolio_service(self, method: str, path: str, **kwargs) -> dict:
        return await self._request_json(f"{self._portfolio_base_url}{path}", method, error_label="Portfolio-Service", **kwargs)

    async def _request_marketdata_service(self, method: str, path: str, **kwargs) -> dict:
        return await self._request_json(f"{self._marketdata_base_url}{path}", method, error_label="Marketdata-Service", **kwargs)

    async def _request_json(self, url: str, method: str, *, json: dict | None = None, params: dict | None = None, expect_no_content: bool = False, error_label: str | None = None) -> dict | list[dict]:
        query = {k: v for k, v in (params or {}).items() if v is not None}
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.request(method, url, json=json, params=query)
        except httpx.RequestError as exc:
            if error_label:
                raise HTTPException(status_code=502, detail=f"{error_label} ist derzeit nicht erreichbar. Bitte später erneut versuchen.") from exc
            raise

        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=self._error_detail(response))
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
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(f"{self._analytics_base_url}/api/v1/analytics/persons/{person_id}/{endpoint}")
        response.raise_for_status()
        return response.json()["data"]

    async def _health_probe(self, service: str, url: str) -> HealthDependency:
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(url)
            return HealthDependency(service=service, status="up" if response.status_code == 200 else "down", detail=None if response.status_code == 200 else f"HTTP {response.status_code}")
        except Exception as exc:
            return HealthDependency(service=service, status="down", detail=str(exc))
