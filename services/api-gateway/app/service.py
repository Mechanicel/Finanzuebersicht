from __future__ import annotations

from uuid import UUID

import httpx

from app.models import (
    AccountReadModel,
    DashboardReadModel,
    GatewayHealthReadModel,
    HealthDependency,
    PersonListItem,
    PersonListReadModel,
    PortfolioReadModel,
)

PERSONS = [
    PersonListItem(
        person_id=UUID("00000000-0000-0000-0000-000000000101"), display_name="Anna Muster"
    ),
    PersonListItem(
        person_id=UUID("00000000-0000-0000-0000-000000000102"), display_name="Max Beispiel"
    ),
]

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
    UUID("00000000-0000-0000-0000-000000000102"): [
        AccountReadModel(
            account_id=UUID("10000000-0000-0000-0000-000000000003"),
            name="Depot Max",
            type="brokerage",
            balance=95400,
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
    UUID("00000000-0000-0000-0000-000000000102"): [
        PortfolioReadModel(
            portfolio_id=UUID("20000000-0000-0000-0000-000000000002"),
            label="Growth",
            total_value=95400,
        )
    ],
}


class GatewayService:
    def __init__(self, analytics_base_url: str, timeout_seconds: float) -> None:
        self._analytics_base_url = analytics_base_url.rstrip("/")
        self._timeout = timeout_seconds

    async def list_persons(self) -> PersonListReadModel:
        return PersonListReadModel(items=PERSONS, total=len(PERSONS))

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
            HealthDependency(
                service="person-service", status="stubbed", detail="BFF list/person use-case mapped"
            ),
            HealthDependency(
                service="portfolio-service",
                status="stubbed",
                detail="BFF portfolio use-case mapped",
            ),
            HealthDependency(
                service="account-service", status="stubbed", detail="BFF account use-case mapped"
            ),
        ]
        status = "up" if dependencies[0].status == "up" else "degraded"
        return GatewayHealthReadModel(status=status, dependencies=dependencies)

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
