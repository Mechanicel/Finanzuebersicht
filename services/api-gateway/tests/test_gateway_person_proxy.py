# ruff: noqa: E402
from __future__ import annotations

import sys
from pathlib import Path
from uuid import UUID

import pytest
from fastapi import HTTPException

ROOT = Path(__file__).resolve().parents[3]
SERVICE_ROOT = Path(__file__).resolve().parents[1]
SHARED_SRC = ROOT / "shared" / "src"
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))
if str(SHARED_SRC) not in sys.path:
    sys.path.insert(0, str(SHARED_SRC))

from app.models import PersonCreatePayload, PersonUpdatePayload
from app.service import GatewayService


@pytest.mark.anyio
async def test_gateway_person_crud_forwarding(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, str, dict | None, dict | None]] = []

    async def fake_request(
        self,
        method: str,
        url: str,
        json: dict | None = None,
        params: dict | None = None,
    ):
        calls.append((method, url, json, params))

        class Response:
            status_code = 200

            @staticmethod
            def json() -> dict:
                person_payload = {
                    "person_id": "00000000-0000-0000-0000-000000000101",
                    "first_name": "Anna",
                    "last_name": "Muster",
                    "email": "anna@example.com",
                    "created_at": "2026-01-01T00:00:00+00:00",
                    "updated_at": "2026-01-01T00:00:00+00:00",
                }
                if method == "GET" and url.endswith("/api/v1/persons"):
                    return {
                        "data": {
                            "items": [
                                {
                                    "person_id": person_payload["person_id"],
                                    "first_name": "Anna",
                                    "last_name": "Muster",
                                    "email": "anna@example.com",
                                    "bank_count": 0,
                                    "allowance_total": "0.00",
                                }
                            ],
                            "pagination": {"limit": 10, "offset": 0, "returned": 1, "total": 1},
                        }
                    }
                if method == "GET" and "/api/v1/persons/" in url:
                    return {
                        "data": {
                            "person": person_payload,
                            "stats": {
                                "person_id": person_payload["person_id"],
                                "first_name": "Anna",
                                "last_name": "Muster",
                                "email": "anna@example.com",
                                "bank_count": 0,
                                "allowance_total": "0.00",
                            },
                        }
                    }
                return {"data": person_payload}

            text = ""

        return Response()

    monkeypatch.setattr("httpx.AsyncClient.request", fake_request)

    service = GatewayService(
        analytics_base_url="http://analytics",
        person_base_url="http://localhost:8002",
        timeout_seconds=1.0,
    )
    person_id = UUID("00000000-0000-0000-0000-000000000101")

    await service.list_persons(q="anna", limit=10, offset=0)
    await service.create_person(PersonCreatePayload(first_name="Anna", last_name="Muster", email="anna@example.com"))
    await service.get_person(person_id)
    await service.update_person(person_id, PersonUpdatePayload(last_name="Neu"))
    await service.delete_person(person_id)

    assert calls[0][0] == "GET"
    assert calls[0][1].endswith("/api/v1/persons")
    assert calls[0][3] == {"q": "anna", "limit": 10, "offset": 0}
    assert calls[1][0] == "POST"
    assert calls[2][1].endswith(f"/api/v1/persons/{person_id}")
    assert calls[3][0] == "PATCH"
    assert calls[4][0] == "DELETE"


@pytest.mark.anyio
async def test_gateway_person_errors_are_translated(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_request(self, method: str, url: str, json: dict | None = None, params: dict | None = None):
        class Response:
            status_code = 409

            @staticmethod
            def json() -> dict:
                return {"detail": "Person bereits vorhanden"}

            text = "Person bereits vorhanden"

        return Response()

    monkeypatch.setattr("httpx.AsyncClient.request", fake_request)

    service = GatewayService(
        analytics_base_url="http://analytics",
        person_base_url="http://localhost:8002",
        timeout_seconds=1.0,
    )

    with pytest.raises(HTTPException) as exc:
        await service.create_person(PersonCreatePayload(first_name="Anna", last_name="Muster"))

    assert exc.value.status_code == 409
    assert exc.value.detail == "Person bereits vorhanden"
