# ruff: noqa: E402
from __future__ import annotations

import sys
from pathlib import Path
from uuid import UUID

ROOT = Path(__file__).resolve().parents[3]
SHARED_SRC = ROOT / "shared" / "src"
if str(SHARED_SRC) not in sys.path:
    sys.path.insert(0, str(SHARED_SRC))

SERVICE_ROOT = Path(__file__).resolve().parents[1]

if "app" in sys.modules:
    del sys.modules["app"]

if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from fastapi import HTTPException

from app.dependencies import get_gateway_service
from app.main import app
from app.models import DashboardReadModel, GatewayHealthReadModel, HealthDependency
from finanzuebersicht_shared.testing import assert_standard_health_payload, create_test_client

PERSON_ID = UUID("00000000-0000-0000-0000-000000000101")


class StubGatewayService:
    async def list_persons(
        self,
        *,
        q: str | None = None,
        sort_by: str | None = None,
        direction: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> dict:
        return {
            "items": [
                {
                    "person_id": str(PERSON_ID),
                    "first_name": "Anna",
                    "last_name": "Muster",
                    "email": "anna@example.com",
                    "bank_count": 1,
                    "allowance_total": "100.00",
                }
            ],
            "pagination": {"limit": 25, "offset": 0, "returned": 1, "total": 1},
        }

    async def create_person(self, person) -> dict:
        if person.first_name.lower() == "duplicate":
            raise HTTPException(status_code=409, detail="Person bereits vorhanden")
        return {
            "person_id": str(PERSON_ID),
            "first_name": person.first_name,
            "last_name": person.last_name,
            "email": person.email,
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "2026-01-01T00:00:00+00:00",
        }

    async def get_person(self, person_id: UUID) -> dict:
        return {
            "person": {
                "person_id": str(person_id),
                "first_name": "Anna",
                "last_name": "Muster",
                "email": "anna@example.com",
                "created_at": "2026-01-01T00:00:00+00:00",
                "updated_at": "2026-01-01T00:00:00+00:00",
            },
            "stats": {
                "person_id": str(person_id),
                "first_name": "Anna",
                "last_name": "Muster",
                "email": "anna@example.com",
                "bank_count": 1,
                "allowance_total": "100.00",
            },
        }

    async def update_person(self, person_id: UUID, person) -> dict:
        return {
            "person_id": str(person_id),
            "first_name": person.first_name or "Anna",
            "last_name": person.last_name or "Muster",
            "email": person.email or "anna@example.com",
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "2026-01-02T00:00:00+00:00",
        }

    async def delete_person(self, person_id: UUID) -> None:
        if str(person_id).endswith("999"):
            raise HTTPException(status_code=404, detail="Person nicht gefunden")

    async def get_dashboard(self, person_id: UUID) -> DashboardReadModel:
        return DashboardReadModel(
            person_id=person_id,
            overview={"labels": ["2026-02-28"], "kpis": [{"key": "wealth", "value": 1}]},
            allocation={"slices": [{"label": "Stocks", "value": 1}]},
            metrics={"kpis": [{"key": "metric"}]},
            timeseries={"series": [{"points": [{"x": "2026-02-28", "y": 1}]}]},
            kpis=[{"key": "wealth", "value": 1}],
        )

    async def list_accounts(self, person_id: UUID) -> list[dict]:
        return [
            {
                "account_id": "10000000-0000-0000-0000-000000000001",
                "name": "Depot",
                "type": "brokerage",
                "balance": 10,
            }
        ]

    async def list_portfolios(self, person_id: UUID) -> list[dict]:
        return [
            {
                "portfolio_id": "20000000-0000-0000-0000-000000000001",
                "label": "Core",
                "total_value": 10,
            }
        ]

    async def get_analytics_overview(self, person_id: UUID) -> dict:
        return {"labels": ["2026-02-28"], "series": []}


    async def list_banks(self) -> dict:
        return {
            "items": [
                {
                    "bank_id": "30000000-0000-0000-0000-000000000001",
                    "name": "Musterbank",
                    "bic": "DEUTDEFFXXX",
                    "blz": "12345678",
                    "country_code": "DE",
                }
            ],
            "total": 1,
        }

    async def create_bank(self, payload) -> dict:
        return {
            "bank_id": "30000000-0000-0000-0000-000000000001",
            "name": payload.name,
            "bic": payload.bic,
            "blz": payload.blz,
            "country_code": payload.country_code,
        }

    async def dependency_health(self, person_id: UUID) -> GatewayHealthReadModel:
        return GatewayHealthReadModel(
            status="up", dependencies=[HealthDependency(service="analytics-service", status="up")]
        )


def test_health_endpoint() -> None:
    client = create_test_client(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert_standard_health_payload(response.json(), "api-gateway")


def test_app_endpoints_for_vue_pages() -> None:
    app.dependency_overrides[get_gateway_service] = lambda: StubGatewayService()
    client = create_test_client(app)

    assert client.get("/api/v1/app/persons").status_code == 200
    assert client.get("/api/v1/app/persons", params={"q": "Anna", "limit": 10, "offset": 0}).status_code == 200
    assert client.post("/api/v1/app/persons", json={"first_name": "Anna", "last_name": "Muster"}).status_code == 201
    assert client.get(f"/api/v1/app/persons/{PERSON_ID}").status_code == 200
    assert client.patch(f"/api/v1/app/persons/{PERSON_ID}", json={"last_name": "Neu"}).status_code == 200
    assert client.delete(f"/api/v1/app/persons/{PERSON_ID}").status_code == 204

    assert client.get("/api/v1/app/banks").status_code == 200
    assert client.post(
        "/api/v1/app/banks",
        json={"name": "Neue Bank", "bic": "DEUTDEFFXXX", "blz": "12345678", "country_code": "DE"},
    ).status_code == 201

    assert client.get(f"/api/v1/app/persons/{PERSON_ID}/dashboard").status_code == 200
    assert client.get(f"/api/v1/app/persons/{PERSON_ID}/accounts").status_code == 200
    assert client.get(f"/api/v1/app/persons/{PERSON_ID}/portfolios").status_code == 200
    assert client.get(f"/api/v1/app/persons/{PERSON_ID}/analytics/overview").status_code == 200

    payload = client.get(f"/api/v1/app/persons/{PERSON_ID}/dashboard").json()["data"]
    assert payload["overview"]["labels"]
    assert payload["kpis"]

    app.dependency_overrides.clear()


def test_person_errors_are_forwarded() -> None:
    app.dependency_overrides[get_gateway_service] = lambda: StubGatewayService()
    client = create_test_client(app)

    response = client.post(
        "/api/v1/app/persons",
        json={"first_name": "Duplicate", "last_name": "Person", "email": "x@example.com"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Person bereits vorhanden"
    app.dependency_overrides.clear()


def test_gateway_dependency_health_endpoint() -> None:
    app.dependency_overrides[get_gateway_service] = lambda: StubGatewayService()
    client = create_test_client(app)

    response = client.get(f"/api/v1/app/persons/{PERSON_ID}/health")

    assert response.status_code == 200
    assert response.json()["data"]["dependencies"][0]["service"] == "analytics-service"
    app.dependency_overrides.clear()
