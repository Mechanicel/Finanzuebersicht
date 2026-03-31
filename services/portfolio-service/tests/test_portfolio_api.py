# ruff: noqa: E402
from __future__ import annotations

import sys
from pathlib import Path
from uuid import uuid4

import pytest

ROOT = Path(__file__).resolve().parents[3]
SHARED_SRC = ROOT / "shared" / "src"
if str(SHARED_SRC) not in sys.path:
    sys.path.append(str(SHARED_SRC))

SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.append(str(SERVICE_ROOT))

from finanzuebersicht_shared.testing import assert_standard_health_payload, create_test_client

from app.dependencies import get_repository
from app.main import app


@pytest.fixture(autouse=True)
def reset_repo() -> None:
    get_repository.cache_clear()


def test_health_and_ready_endpoints() -> None:
    client = create_test_client(app)
    health = client.get("/health")
    ready = client.get("/ready")

    assert health.status_code == 200
    assert_standard_health_payload(health.json(), "portfolio-service")
    assert ready.status_code == 200
    assert_standard_health_payload(ready.json(), "portfolio-service")


def test_portfolio_and_holding_crud_flow() -> None:
    client = create_test_client(app)
    person_id = str(uuid4())

    created = client.post("/api/v1/portfolios", json={"person_id": person_id, "display_name": "Langfrist Depot"})
    assert created.status_code == 201
    portfolio_id = created.json()["data"]["portfolio_id"]

    listed = client.get(f"/api/v1/persons/{person_id}/portfolios")
    assert listed.status_code == 200
    assert listed.json()["data"]["total"] == 1

    add_holding = client.post(
        f"/api/v1/portfolios/{portfolio_id}/holdings",
        json={
            "symbol": "AAPL",
            "isin": "US0378331005",
            "wkn": "865985",
            "company_name": "Apple Inc.",
            "display_name": "Apple",
            "quantity": 3,
            "acquisition_price": 145.5,
            "currency": "usd",
            "buy_date": "2026-03-12",
            "notes": "Sparplan",
        },
    )
    assert add_holding.status_code == 201
    holding_id = add_holding.json()["data"]["holding_id"]
    assert add_holding.json()["data"]["currency"] == "USD"

    detail = client.get(f"/api/v1/portfolios/{portfolio_id}")
    assert detail.status_code == 200
    assert len(detail.json()["data"]["holdings"]) == 1

    patch = client.patch(
        f"/api/v1/portfolios/{portfolio_id}/holdings/{holding_id}",
        json={"quantity": 4, "notes": "Aufgestockt"},
    )
    assert patch.status_code == 200
    assert patch.json()["data"]["quantity"] == 4

    delete = client.delete(f"/api/v1/portfolios/{portfolio_id}/holdings/{holding_id}")
    assert delete.status_code == 204

    detail_after = client.get(f"/api/v1/portfolios/{portfolio_id}")
    assert detail_after.status_code == 200
    assert detail_after.json()["data"]["holdings"] == []


def test_not_found_and_validation() -> None:
    client = create_test_client(app)
    unknown_portfolio = str(uuid4())
    unknown_holding = str(uuid4())

    missing_portfolio = client.get(f"/api/v1/portfolios/{unknown_portfolio}")
    assert missing_portfolio.status_code == 404

    patch_missing = client.patch(
        f"/api/v1/portfolios/{unknown_portfolio}/holdings/{unknown_holding}",
        json={"quantity": 10},
    )
    assert patch_missing.status_code == 404

    invalid_create = client.post(
        "/api/v1/portfolios",
        json={"person_id": str(uuid4()), "display_name": "   "},
    )
    assert invalid_create.status_code == 422

    invalid_holding = client.post(
        f"/api/v1/portfolios/{unknown_portfolio}/holdings",
        json={
            "symbol": "AAPL",
            "quantity": 0,
            "acquisition_price": 10,
            "currency": "EUR",
            "buy_date": "2026-03-31",
        },
    )
    assert invalid_holding.status_code in {404, 422}
