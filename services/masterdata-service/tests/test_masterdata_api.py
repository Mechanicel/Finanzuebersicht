# ruff: noqa: E402
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SHARED_SRC = ROOT / "shared" / "src"
if str(SHARED_SRC) not in sys.path:
    sys.path.append(str(SHARED_SRC))

SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.append(str(SERVICE_ROOT))

import pytest
from finanzuebersicht_shared.testing import create_test_client

from app.dependencies import get_repository
from app.main import app


@pytest.fixture(autouse=True)
def reset_repo() -> None:
    get_repository.cache_clear()


def test_banks_crud() -> None:
    client = create_test_client(app)

    create_response = client.post(
        "/api/v1/banks",
        json={
            "name": "Testbank",
            "bic": "DEUTDEFFXXX",
            "blz": "12345678",
            "country_code": "DE",
        },
    )
    assert create_response.status_code == 201
    bank_id = create_response.json()["data"]["bank_id"]

    get_response = client.get(f"/api/v1/banks/{bank_id}")
    assert get_response.status_code == 200
    assert get_response.json()["data"]["name"] == "Testbank"

    patch_response = client.patch(f"/api/v1/banks/{bank_id}", json={"name": "Neue Testbank"})
    assert patch_response.status_code == 200
    assert patch_response.json()["data"]["name"] == "Neue Testbank"

    list_response = client.get("/api/v1/banks")
    assert list_response.status_code == 200
    assert list_response.json()["data"]["total"] == 1

    delete_response = client.delete(f"/api/v1/banks/{bank_id}")
    assert delete_response.status_code == 204

    missing_response = client.get(f"/api/v1/banks/{bank_id}")
    assert missing_response.status_code == 404


def test_banks_validation_duplicate_bic() -> None:
    client = create_test_client(app)

    payload = {
        "name": "A",
        "bic": "MARKDEF1100",
        "blz": "11112222",
        "country_code": "DE",
    }
    assert client.post("/api/v1/banks", json=payload).status_code == 201

    duplicate_response = client.post(
        "/api/v1/banks",
        json={"name": "B", "bic": "MARKDEF1100", "blz": "33334444", "country_code": "DE"},
    )
    assert duplicate_response.status_code == 409


def test_account_types_crud_and_schema_sorting() -> None:
    client = create_test_client(app)

    create_response = client.post(
        "/api/v1/account-types",
        json={
            "key": "girokonto",
            "name": "Girokonto",
            "description": "Standardkonto",
            "schema_fields": [
                {
                    "feldname": "iban",
                    "label": "IBAN",
                    "typ": "text",
                    "required": True,
                    "placeholder": "DE...",
                    "default": None,
                    "options": [],
                    "help_text": "Internationale Kontonummer",
                    "order": 20,
                },
                {
                    "feldname": "waehrung",
                    "label": "Währung",
                    "typ": "select",
                    "required": True,
                    "placeholder": None,
                    "default": "EUR",
                    "options": [
                        {"value": "EUR", "label": "Euro"},
                        {"value": "USD", "label": "US Dollar"},
                    ],
                    "help_text": None,
                    "order": 10,
                },
            ],
        },
    )
    assert create_response.status_code == 201
    body = create_response.json()["data"]
    assert body["schema_fields"][0]["feldname"] == "waehrung"
    account_type_id = body["account_type_id"]

    get_response = client.get(f"/api/v1/account-types/{account_type_id}")
    assert get_response.status_code == 200

    patch_response = client.patch(
        f"/api/v1/account-types/{account_type_id}", json={"name": "Privat-Girokonto"}
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["data"]["name"] == "Privat-Girokonto"

    list_response = client.get("/api/v1/account-types")
    assert list_response.status_code == 200
    assert list_response.json()["data"]["total"] == 1

    delete_response = client.delete(f"/api/v1/account-types/{account_type_id}")
    assert delete_response.status_code == 204


def test_account_type_validation_select_requires_options() -> None:
    client = create_test_client(app)

    response = client.post(
        "/api/v1/account-types",
        json={
            "key": "sparkonto",
            "name": "Sparkonto",
            "schema_fields": [
                {
                    "feldname": "anlageart",
                    "label": "Anlageart",
                    "typ": "select",
                    "required": True,
                    "placeholder": None,
                    "default": None,
                    "options": [],
                    "help_text": None,
                    "order": 1,
                }
            ],
        },
    )
    assert response.status_code == 422


def test_health_endpoint() -> None:
    client = create_test_client(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["service"] == "masterdata-service"
