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


def test_holdings_and_portfolio_endpoints() -> None:
    client = create_test_client(app)
    account_id = str(uuid4())

    put_payload = {
        "holdings": [
            {"isin": "DE0005557508", "quantity": 12.5, "instrument_name": "Deutsche Telekom"},
            {"isin": "US0378331005", "quantity": 3, "instrument_name": "Apple"},
        ]
    }
    put_result = client.put(f"/api/v1/accounts/{account_id}/portfolio/holdings", json=put_payload)
    assert put_result.status_code == 200
    assert put_result.json()["data"]["holdings_count"] == 2

    get_holdings = client.get(f"/api/v1/accounts/{account_id}/portfolio/holdings")
    assert get_holdings.status_code == 200
    assert get_holdings.json()["data"]["total_quantity_summary"] == 15.5

    compact = client.get(
        f"/api/v1/accounts/{account_id}/portfolio/holdings",
        params={"response_mode": "compact"},
    )
    assert compact.status_code == 200
    assert compact.json()["data"]["holdings"] == []

    account_portfolio = client.get(f"/api/v1/accounts/{account_id}/portfolio")
    assert account_portfolio.status_code == 200
    portfolio_id = account_portfolio.json()["data"]["portfolio_id"]
    assert account_portfolio.json()["data"]["display_name"].startswith("Depot")

    by_portfolio_id = client.get(f"/api/v1/portfolios/{portfolio_id}")
    assert by_portfolio_id.status_code == 200
    assert by_portfolio_id.json()["data"]["account_id"] == account_id


def test_snapshot_flow_and_query_parameters() -> None:
    client = create_test_client(app)
    account_id = str(uuid4())

    snapshot_a = {
        "snapshot_date": "2026-01-15",
        "note": "Monatsanfang",
        "holdings": [
            {"isin": "DE0005557508", "quantity": 10},
            {"isin": "US0378331005", "quantity": 5},
        ],
    }
    snapshot_b = {
        "snapshot_date": "2026-03-10",
        "holdings": [
            {"isin": "DE0005557508", "quantity": 11},
        ],
    }

    created_a = client.post(f"/api/v1/accounts/{account_id}/portfolio/snapshots", json=snapshot_a)
    created_b = client.post(f"/api/v1/accounts/{account_id}/portfolio/snapshots", json=snapshot_b)
    assert created_a.status_code == 201
    assert created_b.status_code == 201

    all_snaps = client.get(f"/api/v1/accounts/{account_id}/portfolio/snapshots")
    assert all_snaps.status_code == 200
    assert len(all_snaps.json()["data"]["snapshots"]) == 2

    latest_only = client.get(
        f"/api/v1/accounts/{account_id}/portfolio/snapshots",
        params={"include_history": False},
    )
    assert latest_only.status_code == 200
    assert len(latest_only.json()["data"]["snapshots"]) == 1

    as_of = client.get(
        f"/api/v1/accounts/{account_id}/portfolio/snapshots",
        params={"as_of": "2026-02-01"},
    )
    assert as_of.status_code == 200
    assert len(as_of.json()["data"]["snapshots"]) == 1

    compact = client.get(
        f"/api/v1/accounts/{account_id}/portfolio/snapshots",
        params={"response_mode": "compact"},
    )
    assert compact.status_code == 200
    assert compact.json()["data"]["snapshots"] == []
    assert compact.json()["data"]["latest_snapshot_summary"]["holdings_count"] == 1


def test_validation_isin_quantity_duplicates_and_empty_holdings() -> None:
    client = create_test_client(app)
    account_id = str(uuid4())

    invalid_isin = client.put(
        f"/api/v1/accounts/{account_id}/portfolio/holdings",
        json={"holdings": [{"isin": "INVALID", "quantity": 2}]},
    )
    assert invalid_isin.status_code == 422

    invalid_quantity = client.put(
        f"/api/v1/accounts/{account_id}/portfolio/holdings",
        json={"holdings": [{"isin": "DE0005557508", "quantity": 0}]},
    )
    assert invalid_quantity.status_code == 422

    duplicate = client.put(
        f"/api/v1/accounts/{account_id}/portfolio/holdings",
        json={
            "holdings": [
                {"isin": "DE0005557508", "quantity": 2},
                {"isin": "DE0005557508", "quantity": 3},
            ]
        },
    )
    assert duplicate.status_code == 422

    empty_holdings = client.put(
        f"/api/v1/accounts/{account_id}/portfolio/holdings",
        json={"holdings": []},
    )
    assert empty_holdings.status_code == 422

    duplicate_snapshot = client.post(
        f"/api/v1/accounts/{account_id}/portfolio/snapshots",
        json={
            "snapshot_date": "2026-02-02",
            "holdings": [
                {"isin": "DE0005557508", "quantity": 1},
                {"isin": "DE0005557508", "quantity": 5},
            ],
        },
    )
    assert duplicate_snapshot.status_code == 422
