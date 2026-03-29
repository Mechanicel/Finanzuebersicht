# ruff: noqa: E402
from __future__ import annotations

import sys
from pathlib import Path
from uuid import UUID

ROOT = Path(__file__).resolve().parents[3]
SHARED_SRC = ROOT / "shared" / "src"
if str(SHARED_SRC) not in sys.path:
    sys.path.append(str(SHARED_SRC))

SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.append(str(SERVICE_ROOT))

from app.dependencies import get_gateway_service
from app.main import app
from app.models import (
    DashboardReadModel,
    GatewayHealthReadModel,
    HealthDependency,
    PersonListItem,
    PersonListReadModel,
)
from finanzuebersicht_shared.testing import assert_standard_health_payload, create_test_client

PERSON_ID = UUID("00000000-0000-0000-0000-000000000101")


class StubGatewayService:
    async def list_persons(self) -> PersonListReadModel:
        return PersonListReadModel(
            items=[PersonListItem(person_id=PERSON_ID, display_name="Anna Muster")], total=1
        )

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
    assert client.get(f"/api/v1/app/persons/{PERSON_ID}/dashboard").status_code == 200
    assert client.get(f"/api/v1/app/persons/{PERSON_ID}/accounts").status_code == 200
    assert client.get(f"/api/v1/app/persons/{PERSON_ID}/portfolios").status_code == 200
    assert client.get(f"/api/v1/app/persons/{PERSON_ID}/analytics/overview").status_code == 200

    payload = client.get(f"/api/v1/app/persons/{PERSON_ID}/dashboard").json()["data"]
    assert payload["overview"]["labels"]
    assert payload["kpis"]

    app.dependency_overrides.clear()


def test_gateway_dependency_health_endpoint() -> None:
    app.dependency_overrides[get_gateway_service] = lambda: StubGatewayService()
    client = create_test_client(app)

    response = client.get(f"/api/v1/app/persons/{PERSON_ID}/health")

    assert response.status_code == 200
    assert response.json()["data"]["dependencies"][0]["service"] == "analytics-service"
    app.dependency_overrides.clear()
