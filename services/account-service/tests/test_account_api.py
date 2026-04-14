# ruff: noqa: E402
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SHARED_SRC = ROOT / "shared" / "src"
if str(SHARED_SRC) not in sys.path:
    sys.path.insert(0, str(SHARED_SRC))

SERVICE_ROOT = Path(__file__).resolve().parents[1]

if "app" in sys.modules:
    del sys.modules["app"]

if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from app.main import app
from finanzuebersicht_shared.testing import create_test_client


def test_account_endpoints_crud_flow() -> None:
    client = create_test_client(app)
    person_id = "00000000-0000-0000-0000-000000000101"

    create_response = client.post(
        f"/api/v1/persons/{person_id}/accounts",
        json={
            "bank_id": "30000000-0000-0000-0000-000000000001",
            "account_type": "depot",
            "label": "Depot Nord",
            "balance": "14500.34",
            "currency": "EUR",
            "depot_number": "DEP-11",
            "portfolio_id": "20000000-0000-0000-0000-000000000001",
        },
    )
    assert create_response.status_code == 201
    created_payload = create_response.json()["data"]
    account_id = created_payload["account_id"]
    assert created_payload["person_id"] == person_id
    assert created_payload["balance"] == "14500.34"
    assert created_payload["portfolio_id"] == "20000000-0000-0000-0000-000000000001"

    list_response = client.get(f"/api/v1/persons/{person_id}/accounts")
    assert list_response.status_code == 200
    assert list_response.json()["data"][0]["account_id"] == account_id

    get_response = client.get(f"/api/v1/persons/{person_id}/accounts/{account_id}")
    assert get_response.status_code == 200
    assert get_response.json()["data"]["label"] == "Depot Nord"

    patch_response = client.patch(
        f"/api/v1/persons/{person_id}/accounts/{account_id}",
        json={
            "label": "Depot Nord aktualisiert",
            "balance": "15000.00",
            "account_type": "girokonto",
        },
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["data"]["label"] == "Depot Nord aktualisiert"
    assert patch_response.json()["data"]["account_type"] == "girokonto"
    assert patch_response.json()["data"]["balance"] == "15000.00"

    delete_response = client.delete(f"/api/v1/persons/{person_id}/accounts/{account_id}")
    assert delete_response.status_code == 204

    missing_after_delete = client.get(f"/api/v1/persons/{person_id}/accounts/{account_id}")
    assert missing_after_delete.status_code == 404


def test_account_patch_missing_payload_and_unknown_account() -> None:
    client = create_test_client(app)
    person_id = "00000000-0000-0000-0000-000000000101"

    empty_patch = client.patch(
        f"/api/v1/persons/{person_id}/accounts/10000000-0000-0000-0000-000000000001",
        json={},
    )
    assert empty_patch.status_code == 422

    missing_account = client.get(
        f"/api/v1/persons/{person_id}/accounts/10000000-0000-0000-0000-000000000001"
    )
    assert missing_account.status_code == 404

    missing_delete = client.delete(
        f"/api/v1/persons/{person_id}/accounts/10000000-0000-0000-0000-000000000001"
    )
    assert missing_delete.status_code == 404
