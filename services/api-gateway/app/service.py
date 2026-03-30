from __future__ import annotations

from uuid import UUID

import httpx
from fastapi import HTTPException

from app.models import (
    AccountReadModel,
    AssignmentListReadModel,
    BankCreatePayload,
    BankListReadModel,
    BankReadModel,
    DashboardReadModel,
    GatewayHealthReadModel,
    HealthDependency,
    PersonCreatePayload,
    PersonDetailReadModel,
    PersonListReadModel,
    PersonReadModel,
    PersonUpdatePayload,
    PersonBankAssignmentReadModel,
    PortfolioReadModel,
)

PERSON_ACCOUNTS: dict[UUID, list[AccountReadModel]] = {
    UUID("00000000-0000-0000-0000-000000000101"): [
        AccountReadModel(
            account_id=UUID("10000000-0000-0000-0000-000000000001"),
            name="Depot Anna",
            type="brokerage",
            balance=134900,
        ),
        AccountReadModel(
            account_id=UUID("10000000-0000-0000-0000-000000000002"),
            name="Tagesgeld Anna",
            type="cash",
            balance=21000,
        ),
    ],
}

PERSON_PORTFOLIOS: dict[UUID, list[PortfolioReadModel]] = {
    UUID("00000000-0000-0000-0000-000000000101"): [
        PortfolioReadModel(
            portfolio_id=UUID("20000000-0000-0000-0000-000000000001"),
            label="Global Core",
            total_value=134900,
        )
    ],
}


class GatewayService:
    def __init__(
        self,
        analytics_base_url: str,
        person_base_url: str,
        masterdata_base_url: str,
        timeout_seconds: float,
    ) -> None:
        self._analytics_base_url = analytics_base_url.rstrip("/")
        self._person_base_url = person_base_url.rstrip("/")
        self._masterdata_base_url = masterdata_base_url.rstrip("/")
        self._timeout = timeout_seconds

    async def list_persons(
        self,
        *,
        q: str | None = None,
        sort_by: str | None = None,
        direction: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> PersonListReadModel:
        payload = await self._request_person_service(
            "GET",
            "/api/v1/persons",
            params={
                "q": q,
                "sort_by": sort_by,
                "direction": direction,
                "limit": limit,
                "offset": offset,
            },
        )
        return PersonListReadModel.model_validate(payload)

    async def create_person(self, person: PersonCreatePayload) -> PersonReadModel:
        payload = await self._request_person_service("POST", "/api/v1/persons", json=person.model_dump())
        return PersonReadModel.model_validate(payload)

    async def get_person(self, person_id: UUID) -> PersonDetailReadModel:
        payload = await self._request_person_service("GET", f"/api/v1/persons/{person_id}")
        return PersonDetailReadModel.model_validate(payload)

    async def update_person(self, person_id: UUID, person: PersonUpdatePayload) -> PersonReadModel:
        payload = await self._request_person_service(
            "PATCH", f"/api/v1/persons/{person_id}", json=person.model_dump(exclude_none=True)
        )
        return PersonReadModel.model_validate(payload)

    async def delete_person(self, person_id: UUID) -> None:
        await self._request_person_service("DELETE", f"/api/v1/persons/{person_id}", expect_no_content=True)

    async def list_person_banks(self, person_id: UUID) -> AssignmentListReadModel:
        payload = await self._request_person_service("GET", f"/api/v1/persons/{person_id}/banks")
        return AssignmentListReadModel.model_validate(payload)

    async def assign_bank(self, person_id: UUID, bank_id: UUID) -> PersonBankAssignmentReadModel:
        payload = await self._request_person_service("POST", f"/api/v1/persons/{person_id}/banks/{bank_id}")
        return PersonBankAssignmentReadModel.model_validate(payload)

    async def unassign_bank(self, person_id: UUID, bank_id: UUID) -> None:
        await self._request_person_service(
            "DELETE",
            f"/api/v1/persons/{person_id}/banks/{bank_id}",
            expect_no_content=True,
        )


    async def list_banks(self) -> BankListReadModel:
        payload = await self._request_masterdata_service("GET", "/api/v1/banks")
        return BankListReadModel.model_validate(payload)

    async def create_bank(self, bank: BankCreatePayload) -> BankReadModel:
        payload = await self._request_masterdata_service("POST", "/api/v1/banks", json=bank.model_dump())
        return BankReadModel.model_validate(payload)

    async def list_accounts(self, person_id: UUID) -> list[AccountReadModel]:
        return PERSON_ACCOUNTS.get(person_id, [])

    async def list_portfolios(self, person_id: UUID) -> list[PortfolioReadModel]:
        return PERSON_PORTFOLIOS.get(person_id, [])

    async def get_analytics_overview(self, person_id: UUID) -> dict:
        return await self._get_analytics_payload(person_id, "overview")

    async def get_dashboard(self, person_id: UUID) -> DashboardReadModel:
        overview = await self._get_analytics_payload(person_id, "overview")
        allocation = await self._get_analytics_payload(person_id, "allocation")
        metrics = await self._get_analytics_payload(person_id, "metrics")
        timeseries = await self._get_analytics_payload(person_id, "timeseries")

        return DashboardReadModel(
            person_id=person_id,
            overview=overview,
            allocation=allocation,
            metrics=metrics,
            timeseries=timeseries,
            kpis=overview.get("kpis", []),
        )

    async def dependency_health(self, person_id: UUID) -> GatewayHealthReadModel:
        dependencies = [
            await self._health_probe("analytics-service", f"{self._analytics_base_url}/health"),
            await self._health_probe("person-service", f"{self._person_base_url}/health"),
            HealthDependency(
                service="portfolio-service",
                status="stubbed",
                detail="BFF portfolio use-case mapped",
            ),
            HealthDependency(
                service="account-service", status="stubbed", detail="BFF account use-case mapped"
            ),
        ]
        status = "up" if all(dep.status in {"up", "stubbed"} for dep in dependencies) else "degraded"
        return GatewayHealthReadModel(status=status, dependencies=dependencies)

    async def _request_person_service(
        self,
        method: str,
        path: str,
        *,
        json: dict | None = None,
        params: dict | None = None,
        expect_no_content: bool = False,
    ) -> dict:
        url = f"{self._person_base_url}{path}"
        query = {key: value for key, value in (params or {}).items() if value is not None}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.request(method, url, json=json, params=query)

        if response.status_code >= 400:
            detail = self._error_detail(response)
            raise HTTPException(status_code=response.status_code, detail=detail)

        if expect_no_content:
            return {}

        return response.json()["data"]

    @staticmethod
    def _error_detail(response: httpx.Response) -> object:
        try:
            data = response.json()
            if isinstance(data, dict) and "detail" in data:
                return data["detail"]
            return data
        except Exception:  # noqa: BLE001
            return response.text


    async def _request_masterdata_service(
        self,
        method: str,
        path: str,
        *,
        json: dict | None = None,
        params: dict | None = None,
        expect_no_content: bool = False,
    ) -> dict:
        url = f"{self._masterdata_base_url}{path}"
        query = {key: value for key, value in (params or {}).items() if value is not None}
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.request(method, url, json=json, params=query)
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=502,
                detail="Masterdata-Service ist derzeit nicht erreichbar. Bitte später erneut versuchen.",
            ) from exc

        if response.status_code >= 400:
            detail = self._error_detail(response)
            raise HTTPException(status_code=response.status_code, detail=detail)

        if expect_no_content:
            return {}

        return response.json()["data"]

    async def _get_analytics_payload(self, person_id: UUID, endpoint: str) -> dict:
        url = f"{self._analytics_base_url}/api/v1/analytics/persons/{person_id}/{endpoint}"
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(url)
        response.raise_for_status()
        return response.json()["data"]

    async def _health_probe(self, service: str, url: str) -> HealthDependency:
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(url)
            if response.status_code == 200:
                return HealthDependency(service=service, status="up")
            return HealthDependency(
                service=service, status="down", detail=f"HTTP {response.status_code}"
            )
        except Exception as exc:  # noqa: BLE001
            return HealthDependency(service=service, status="down", detail=str(exc))
