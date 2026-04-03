# ruff: noqa: E402
from __future__ import annotations

import sys
from pathlib import Path
from uuid import UUID

import pytest
from fastapi import HTTPException
from httpx import ConnectError, Request

ROOT = Path(__file__).resolve().parents[3]
SERVICE_ROOT = Path(__file__).resolve().parents[1]
SHARED_SRC = ROOT / "shared" / "src"
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))
if str(SHARED_SRC) not in sys.path:
    sys.path.insert(0, str(SHARED_SRC))

from app.models import (
    AccountCreatePayload,
    AccountUpdatePayload,
    AllowanceUpsertPayload,
    BankCreatePayload,
    PortfolioCreatePayload,
    PersonCreatePayload,
    PersonUpdatePayload,
)
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
                    "tax_profile": {"tax_country": "DE", "filing_status": "single"},
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
        masterdata_base_url="http://localhost:8001",
        account_base_url="http://localhost:8003",
        portfolio_base_url="http://localhost:8004",
        marketdata_base_url="http://localhost:8005",
        timeout_seconds=1.0,
    )
    person_id = UUID("00000000-0000-0000-0000-000000000101")

    await service.list_persons(q="anna", limit=10, offset=0)
    await service.create_person(
        PersonCreatePayload(
            first_name="Anna",
            last_name="Muster",
            email="anna@example.com",
            tax_profile={"tax_country": "DE", "filing_status": "joint"},
        )
    )
    await service.get_person(person_id)
    await service.update_person(person_id, PersonUpdatePayload(last_name="Neu", tax_profile={"filing_status": "single"}))
    await service.delete_person(person_id)

    assert calls[0][0] == "GET"
    assert calls[0][1].endswith("/api/v1/persons")
    assert calls[0][3] == {"q": "anna", "limit": 10, "offset": 0}
    assert calls[1][0] == "POST"
    assert calls[1][2] == {
        "first_name": "Anna",
        "last_name": "Muster",
        "email": "anna@example.com",
        "tax_profile": {"tax_country": "DE", "filing_status": "joint"},
    }
    assert calls[2][1].endswith(f"/api/v1/persons/{person_id}")
    assert calls[3][0] == "PATCH"
    assert calls[3][2] == {"last_name": "Neu", "tax_profile": {"filing_status": "single"}}
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
        masterdata_base_url="http://localhost:8001",
        account_base_url="http://localhost:8003",
        portfolio_base_url="http://localhost:8004",
        marketdata_base_url="http://localhost:8005",
        timeout_seconds=1.0,
    )

    with pytest.raises(HTTPException) as exc:
        await service.create_person(PersonCreatePayload(first_name="Anna", last_name="Muster"))

    assert exc.value.status_code == 409
    assert exc.value.detail == "Person bereits vorhanden"


@pytest.mark.anyio
async def test_gateway_bank_endpoints_forwarding(monkeypatch: pytest.MonkeyPatch) -> None:
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
            status_code = 200 if method == "GET" else 201

            @staticmethod
            def json() -> dict:
                if method == "GET":
                    return {
                        "data": {
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
                    }
                return {
                    "data": {
                        "bank_id": "30000000-0000-0000-0000-000000000001",
                        "name": "Musterbank",
                        "bic": "DEUTDEFFXXX",
                        "blz": "12345678",
                        "country_code": "DE",
                    }
                }

            text = ""

        return Response()

    monkeypatch.setattr("httpx.AsyncClient.request", fake_request)

    service = GatewayService(
        analytics_base_url="http://analytics",
        person_base_url="http://localhost:8002",
        masterdata_base_url="http://localhost:8001",
        account_base_url="http://localhost:8003",
        portfolio_base_url="http://localhost:8004",
        marketdata_base_url="http://localhost:8005",
        timeout_seconds=1.0,
    )

    listing = await service.list_banks()
    created = await service.create_bank(
        BankCreatePayload(name="Musterbank", bic="DEUTDEFFXXX", blz="12345678", country_code="DE")
    )

    assert listing.total == 1
    assert created.name == "Musterbank"
    assert calls[0][0] == "GET"
    assert calls[0][1].endswith("/api/v1/banks")
    assert calls[1][0] == "POST"
    assert calls[1][1].endswith("/api/v1/banks")


@pytest.mark.anyio
async def test_gateway_person_bank_assignment_forwarding(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, str, dict | None, dict | None]] = []
    person_id = UUID("00000000-0000-0000-0000-000000000101")
    bank_id = UUID("30000000-0000-0000-0000-000000000001")

    async def fake_request(
        self,
        method: str,
        url: str,
        json: dict | None = None,
        params: dict | None = None,
    ):
        calls.append((method, url, json, params))

        class Response:
            status_code = 204 if method == "DELETE" else (201 if method == "POST" else 200)

            @staticmethod
            def json() -> dict:
                if method == "GET":
                    return {
                        "data": {
                            "items": [
                                {
                                    "person_id": str(person_id),
                                    "bank_id": str(bank_id),
                                    "assigned_at": "2026-03-01T08:00:00+00:00",
                                }
                            ],
                            "total": 1,
                        }
                    }
                return {
                    "data": {
                        "person_id": str(person_id),
                        "bank_id": str(bank_id),
                        "assigned_at": "2026-03-01T08:00:00+00:00",
                    }
                }

            text = ""

        return Response()

    monkeypatch.setattr("httpx.AsyncClient.request", fake_request)

    service = GatewayService(
        analytics_base_url="http://analytics",
        person_base_url="http://localhost:8002",
        masterdata_base_url="http://localhost:8001",
        account_base_url="http://localhost:8003",
        portfolio_base_url="http://localhost:8004",
        marketdata_base_url="http://localhost:8005",
        timeout_seconds=1.0,
    )

    listing = await service.list_person_banks(person_id)
    assigned = await service.assign_bank(person_id, bank_id)
    await service.unassign_bank(person_id, bank_id)

    assert listing.total == 1
    assert assigned.bank_id == bank_id
    assert calls[0][0] == "GET"
    assert calls[0][1].endswith(f"/api/v1/persons/{person_id}/banks")
    assert calls[1][0] == "POST"
    assert calls[1][1].endswith(f"/api/v1/persons/{person_id}/banks/{bank_id}")
    assert calls[2][0] == "DELETE"
    assert calls[2][1].endswith(f"/api/v1/persons/{person_id}/banks/{bank_id}")


@pytest.mark.anyio
async def test_gateway_allowances_forwarding(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, str, dict | None, dict | None]] = []
    person_id = UUID("00000000-0000-0000-0000-000000000101")
    bank_id = UUID("30000000-0000-0000-0000-000000000001")

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
                if method == "GET" and url.endswith("/allowances"):
                    return {
                        "data": {
                            "items": [
                                {
                                    "person_id": str(person_id),
                                    "bank_id": str(bank_id),
                                    "tax_year": 2025,
                                    "amount": "200.00",
                                    "currency": "EUR",
                                    "updated_at": "2026-03-01T08:00:00+00:00",
                                }
                            ],
                            "total": 1,
                            "amount_total": "200.00",
                        }
                    }
                if method == "GET" and url.endswith("/allowances/summary"):
                    return {
                        "data": {
                            "person_id": str(person_id),
                            "tax_year": 2025,
                            "banks": [{"bank_id": str(bank_id), "tax_year": 2025, "amount": "200.00"}],
                            "total_amount": "200.00",
                            "annual_limit": "1000.00",
                            "remaining_amount": "800.00",
                            "currency": "EUR",
                            "applied_rule": "DE/single",
                            "tax_profile": {"tax_country": "DE", "filing_status": "single"},
                        }
                    }
                return {
                    "data": {
                        "person_id": str(person_id),
                        "bank_id": str(bank_id),
                        "tax_year": 2025,
                        "amount": "250.00",
                        "currency": "EUR",
                        "updated_at": "2026-03-02T08:00:00+00:00",
                    }
                }

            text = ""

        return Response()

    monkeypatch.setattr("httpx.AsyncClient.request", fake_request)

    service = GatewayService(
        analytics_base_url="http://analytics",
        person_base_url="http://localhost:8002",
        masterdata_base_url="http://localhost:8001",
        account_base_url="http://localhost:8003",
        portfolio_base_url="http://localhost:8004",
        marketdata_base_url="http://localhost:8005",
        timeout_seconds=1.0,
    )

    allowances = await service.list_allowances(person_id, tax_year=2025)
    changed = await service.set_allowance(
        person_id, bank_id, AllowanceUpsertPayload(tax_year=2025, amount="250.00", currency="EUR")
    )
    summary = await service.allowance_summary(person_id, tax_year=2025)

    assert allowances.total == 1
    assert changed.amount == "250.00"
    assert changed.tax_year == 2025
    assert summary.total_amount == "200.00"
    assert summary.annual_limit == "1000.00"
    assert summary.remaining_amount == "800.00"
    assert summary.tax_profile is not None
    assert calls[0][0] == "GET"
    assert calls[0][1].endswith(f"/api/v1/persons/{person_id}/allowances")
    assert calls[0][3] == {"tax_year": 2025}
    assert calls[1][0] == "PUT"
    assert calls[1][1].endswith(f"/api/v1/persons/{person_id}/allowances/{bank_id}")
    assert calls[1][2] == {"tax_year": 2025, "amount": "250.00", "currency": "EUR"}
    assert calls[2][0] == "GET"
    assert calls[2][1].endswith(f"/api/v1/persons/{person_id}/allowances/summary")
    assert calls[2][3] == {"tax_year": 2025}


@pytest.mark.anyio
async def test_gateway_allowance_error_details_are_forwarded(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_request(self, method: str, url: str, json: dict | None = None, params: dict | None = None):
        class Response:
            status_code = 422

            @staticmethod
            def json() -> dict:
                return {
                    "detail": {
                        "error": "allowance_limit_exceeded",
                        "message": "Limit überschritten",
                        "context": {"tax_year": 2025},
                    }
                }

            text = "Limit überschritten"

        return Response()

    monkeypatch.setattr("httpx.AsyncClient.request", fake_request)

    service = GatewayService(
        analytics_base_url="http://analytics",
        person_base_url="http://localhost:8002",
        masterdata_base_url="http://localhost:8001",
        account_base_url="http://localhost:8003",
        portfolio_base_url="http://localhost:8004",
        marketdata_base_url="http://localhost:8005",
        timeout_seconds=1.0,
    )

    with pytest.raises(HTTPException) as exc:
        await service.set_allowance(
            UUID("00000000-0000-0000-0000-000000000101"),
            UUID("30000000-0000-0000-0000-000000000001"),
            AllowanceUpsertPayload(tax_year=2025, amount="1200.00"),
        )

    assert exc.value.status_code == 422
    assert exc.value.detail == {
        "error": "allowance_limit_exceeded",
        "message": "Limit überschritten",
        "context": {"tax_year": 2025},
    }


@pytest.mark.anyio
async def test_gateway_accounts_forwarding(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, str, dict | None, dict | None]] = []
    person_id = UUID("00000000-0000-0000-0000-000000000101")
    account_id = UUID("10000000-0000-0000-0000-000000000001")

    async def fake_request(self, method: str, url: str, json: dict | None = None, params: dict | None = None):
        calls.append((method, url, json, params))

        class Response:
            status_code = 201 if method == "POST" else 200

            @staticmethod
            def json() -> dict:
                return {
                    "data": {
                        "account_id": str(account_id),
                        "person_id": str(person_id),
                        "bank_id": "30000000-0000-0000-0000-000000000001",
                        "account_type": "depot",
                        "label": "Depot A",
                        "balance": "1000.00",
                        "currency": "EUR",
                        "created_at": "2026-03-01T08:00:00+00:00",
                        "updated_at": "2026-03-02T08:00:00+00:00",
                    }
                }

            text = ""

        return Response()

    monkeypatch.setattr("httpx.AsyncClient.request", fake_request)

    service = GatewayService(
        analytics_base_url="http://analytics",
        person_base_url="http://localhost:8002",
        masterdata_base_url="http://localhost:8001",
        account_base_url="http://localhost:8003",
        portfolio_base_url="http://localhost:8004",
        marketdata_base_url="http://localhost:8005",
        timeout_seconds=1.0,
    )

    listed = await service.list_accounts(person_id)
    got = await service.get_account(person_id, account_id)
    created = await service.create_account(
        person_id,
        AccountCreatePayload(
            bank_id=UUID("30000000-0000-0000-0000-000000000001"),
            account_type="depot",
            label="Depot A",
            balance="1000.00",
            currency="EUR",
        ),
    )
    updated = await service.update_account(
        person_id,
        account_id,
        AccountUpdatePayload(label="Depot B", bank_id=UUID("30000000-0000-0000-0000-000000000001")),
    )

    assert listed[0].label == "Depot A"
    assert got.account_type == "depot"
    assert created.person_id == person_id
    assert updated.label == "Depot A"
    assert calls[0][1].endswith(f"/api/v1/persons/{person_id}/accounts")
    assert calls[1][1].endswith(f"/api/v1/persons/{person_id}/accounts/{account_id}")
    assert calls[2][0] == "POST"
    assert calls[3][0] == "PATCH"
    assert calls[2][2] is not None
    assert calls[2][2]["bank_id"] == "30000000-0000-0000-0000-000000000001"
    assert calls[3][2] is not None
    assert calls[3][2]["bank_id"] == "30000000-0000-0000-0000-000000000001"


@pytest.mark.anyio
async def test_gateway_masterdata_connect_error_is_translated(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_request(self, method: str, url: str, json: dict | None = None, params: dict | None = None):
        raise ConnectError("connection failed", request=Request(method, url))

    monkeypatch.setattr("httpx.AsyncClient.request", fake_request)

    service = GatewayService(
        analytics_base_url="http://analytics",
        person_base_url="http://localhost:8002",
        masterdata_base_url="http://localhost:8001",
        account_base_url="http://localhost:8003",
        portfolio_base_url="http://localhost:8004",
        marketdata_base_url="http://localhost:8005",
        timeout_seconds=1.0,
    )

    with pytest.raises(HTTPException) as exc:
        await service.create_bank(
            BankCreatePayload(name="Musterbank", bic="DEUTDEFFXXX", blz="12345678", country_code="DE")
        )

    assert exc.value.status_code == 502
    assert exc.value.detail == "Masterdata-Service ist derzeit nicht erreichbar. Bitte später erneut versuchen."


@pytest.mark.anyio
async def test_gateway_marketdata_forwarding_success(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, str, dict | None, dict | None]] = []

    async def fake_request(self, method: str, url: str, json: dict | None = None, params: dict | None = None):
        calls.append((method, url, json, params))

        class Response:
            status_code = 200

            @staticmethod
            def json() -> dict:
                if url.endswith("/search"):
                    return {"data": {"items": [{"symbol": "AAPL", "name": "Apple Inc."}], "total": 1}}
                if url.endswith("/summary"):
                    return {"data": {"symbol": "AAPL", "currency": "USD"}}
                return {"data": {"symbol": "AAPL", "points": [{"close": 100.0}]}}

            text = ""

        return Response()

    monkeypatch.setattr("httpx.AsyncClient.request", fake_request)

    service = GatewayService(
        analytics_base_url="http://analytics",
        person_base_url="http://localhost:8002",
        masterdata_base_url="http://localhost:8001",
        account_base_url="http://localhost:8003",
        portfolio_base_url="http://localhost:8004",
        marketdata_base_url="http://localhost:8005",
        timeout_seconds=1.0,
    )

    search = await service.search_marketdata_instruments(q="apple", limit=5)
    summary = await service.get_marketdata_summary("AAPL")
    prices = await service.get_marketdata_prices("AAPL", range_value="1mo", interval="1d")
    profile = await service.get_marketdata_profile("AAPL")

    assert search["total"] == 1
    assert summary["symbol"] == "AAPL"
    assert prices["symbol"] == "AAPL"
    assert profile["symbol"] == "AAPL"
    assert calls[0][1].endswith("/api/v1/marketdata/instruments/search")
    assert calls[0][3] == {"q": "apple", "limit": 5}
    assert calls[1][1].endswith("/api/v1/marketdata/instruments/AAPL/summary")
    assert calls[2][1].endswith("/api/v1/marketdata/instruments/AAPL/prices")
    assert calls[2][3] == {"range": "1mo", "interval": "1d"}
    assert calls[3][1].endswith("/api/v1/marketdata/instruments/AAPL/profile")


@pytest.mark.anyio
async def test_gateway_marketdata_404_is_forwarded(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_request(self, method: str, url: str, json: dict | None = None, params: dict | None = None):
        class Response:
            status_code = 404

            @staticmethod
            def json() -> dict:
                return {"detail": "Instrument nicht gefunden"}

            text = "Instrument nicht gefunden"

        return Response()

    monkeypatch.setattr("httpx.AsyncClient.request", fake_request)

    service = GatewayService(
        analytics_base_url="http://analytics",
        person_base_url="http://localhost:8002",
        masterdata_base_url="http://localhost:8001",
        account_base_url="http://localhost:8003",
        portfolio_base_url="http://localhost:8004",
        marketdata_base_url="http://localhost:8005",
        timeout_seconds=1.0,
    )

    with pytest.raises(HTTPException) as exc:
        await service.get_marketdata_summary("UNKNOWN")

    assert exc.value.status_code == 404
    assert exc.value.detail == "Instrument nicht gefunden"


@pytest.mark.anyio
async def test_gateway_marketdata_connect_error_is_translated(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_request(self, method: str, url: str, json: dict | None = None, params: dict | None = None):
        raise ConnectError("connection failed", request=Request(method, url))

    monkeypatch.setattr("httpx.AsyncClient.request", fake_request)

    service = GatewayService(
        analytics_base_url="http://analytics",
        person_base_url="http://localhost:8002",
        masterdata_base_url="http://localhost:8001",
        account_base_url="http://localhost:8003",
        portfolio_base_url="http://localhost:8004",
        marketdata_base_url="http://localhost:8005",
        timeout_seconds=1.0,
    )

    with pytest.raises(HTTPException) as exc:
        await service.get_marketdata_prices("AAPL", range_value="1mo", interval="1d")

    assert exc.value.status_code == 502
    assert exc.value.detail == "Marketdata-Service ist derzeit nicht erreichbar. Bitte später erneut versuchen."

@pytest.mark.anyio
async def test_gateway_portfolio_passthrough(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, str, dict | None]] = []

    async def fake_request(self, method: str, url: str, json: dict | None = None, params: dict | None = None):
        calls.append((method, url, json))

        class Response:
            status_code = 200

            @staticmethod
            def json() -> dict:
                if method == "GET" and "/persons/" in url:
                    return {"data": {"items": [], "total": 0}}
                if method == "POST":
                    return {"data": {"portfolio_id": "20000000-0000-0000-0000-000000000001", "person_id": "00000000-0000-0000-0000-000000000101", "display_name": "Core", "created_at": "2026-01-01T00:00:00+00:00", "updated_at": "2026-01-01T00:00:00+00:00"}}
                return {"data": {"portfolio_id": "20000000-0000-0000-0000-000000000001", "person_id": "00000000-0000-0000-0000-000000000101", "display_name": "Core", "created_at": "2026-01-01T00:00:00+00:00", "updated_at": "2026-01-01T00:00:00+00:00", "holdings": []}}

            text = ""

        return Response()

    monkeypatch.setattr("httpx.AsyncClient.request", fake_request)
    service = GatewayService("http://analytics", "http://person", "http://master", "http://account", "http://portfolio", "http://market", 1.0)
    person_id = UUID("00000000-0000-0000-0000-000000000101")

    await service.list_portfolios(person_id)
    await service.create_portfolio(person_id, PortfolioCreatePayload(display_name="Core"))

    assert calls[0][1].endswith(f"/api/v1/persons/{person_id}/portfolios")
    assert calls[1][1].endswith("/api/v1/portfolios")


@pytest.mark.anyio
async def test_gateway_portfolio_404_and_502(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_404(self, method: str, url: str, json: dict | None = None, params: dict | None = None):
        class Response:
            status_code = 404
            text = "not found"
            @staticmethod
            def json() -> dict:
                return {"detail": "Portfolio nicht gefunden"}
        return Response()

    monkeypatch.setattr("httpx.AsyncClient.request", fake_404)
    service = GatewayService("http://analytics", "http://person", "http://master", "http://account", "http://portfolio", "http://market", 1.0)
    with pytest.raises(HTTPException) as not_found:
        await service.get_portfolio(UUID("20000000-0000-0000-0000-000000000001"))
    assert not_found.value.status_code == 404

    async def fake_error(self, method: str, url: str, json: dict | None = None, params: dict | None = None):
        raise ConnectError("down", request=Request(method, url))

    monkeypatch.setattr("httpx.AsyncClient.request", fake_error)
    with pytest.raises(HTTPException) as upstream:
        await service.list_portfolios(UUID("00000000-0000-0000-0000-000000000101"))
    assert upstream.value.status_code == 502
