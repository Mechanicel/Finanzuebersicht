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
            "tax_profile": {"tax_country": "DE", "filing_status": "single"},
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
                "tax_profile": {"tax_country": "DE", "filing_status": "single"},
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
            "tax_profile": {"tax_country": "DE", "filing_status": "single"},
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "2026-01-02T00:00:00+00:00",
        }

    async def delete_person(self, person_id: UUID) -> None:
        if str(person_id).endswith("999"):
            raise HTTPException(status_code=404, detail="Person nicht gefunden")

    async def list_person_banks(self, person_id: UUID) -> dict:
        return {
            "items": [
                {
                    "person_id": str(person_id),
                    "bank_id": "30000000-0000-0000-0000-000000000001",
                    "assigned_at": "2026-03-01T08:00:00+00:00",
                }
            ],
            "total": 1,
        }

    async def assign_bank(self, person_id: UUID, bank_id: UUID) -> dict:
        if str(bank_id).endswith("999"):
            raise HTTPException(status_code=409, detail="Zuordnung bereits vorhanden")
        return {
            "person_id": str(person_id),
            "bank_id": str(bank_id),
            "assigned_at": "2026-03-01T08:00:00+00:00",
        }

    async def unassign_bank(self, person_id: UUID, bank_id: UUID) -> None:
        if str(bank_id).endswith("999"):
            raise HTTPException(status_code=404, detail="Zuordnung nicht gefunden")

    async def list_allowances(self, person_id: UUID, tax_year: int | None = None) -> dict:
        return {
            "items": [
                {
                    "person_id": str(person_id),
                    "bank_id": "30000000-0000-0000-0000-000000000001",
                    "tax_year": tax_year or 2025,
                    "amount": "100.00",
                    "currency": "EUR",
                    "updated_at": "2026-03-01T08:00:00+00:00",
                }
            ],
            "total": 1,
            "amount_total": "100.00",
        }

    async def set_allowance(self, person_id: UUID, bank_id: UUID, payload) -> dict:
        if str(bank_id).endswith("999"):
            raise HTTPException(status_code=409, detail="Nur für zugeordnete Banken zulässig")
        return {
            "person_id": str(person_id),
            "bank_id": str(bank_id),
            "tax_year": payload.tax_year,
            "amount": payload.amount,
            "currency": "EUR",
            "updated_at": "2026-03-02T08:00:00+00:00",
        }

    async def allowance_summary(self, person_id: UUID, tax_year: int) -> dict:
        return {
            "person_id": str(person_id),
            "tax_year": tax_year,
            "banks": [{"bank_id": "30000000-0000-0000-0000-000000000001", "tax_year": tax_year, "amount": "100.00"}],
            "total_amount": "100.00",
            "annual_limit": "1000.00",
            "remaining_amount": "900.00",
            "currency": "EUR",
            "applied_rule": "DE/single",
            "tax_profile": {"tax_country": "DE", "filing_status": "single"},
        }

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
                "person_id": str(person_id),
                "bank_id": "30000000-0000-0000-0000-000000000001",
                "account_type": "depot",
                "label": "Depot",
                "balance": "10.00",
                "currency": "EUR",
                "created_at": "2026-03-01T08:00:00+00:00",
                "updated_at": "2026-03-01T08:00:00+00:00",
            }
        ]

    async def get_account(self, person_id: UUID, account_id: UUID) -> dict:
        return (await self.list_accounts(person_id))[0]

    async def create_account(self, person_id: UUID, payload) -> dict:
        return {
            "account_id": "10000000-0000-0000-0000-000000000009",
            "person_id": str(person_id),
            "bank_id": str(payload.bank_id),
            "account_type": payload.account_type,
            "label": payload.label,
            "balance": payload.balance,
            "currency": payload.currency,
            "created_at": "2026-03-01T08:00:00+00:00",
            "updated_at": "2026-03-01T08:00:00+00:00",
        }

    async def update_account(self, person_id: UUID, account_id: UUID, payload) -> dict:
        account = await self.get_account(person_id, account_id)
        account.update(payload.model_dump(exclude_none=True))
        account["updated_at"] = "2026-03-02T08:00:00+00:00"
        return account

    async def delete_account(self, person_id: UUID, account_id: UUID) -> None:
        return None

    async def list_portfolios(self, person_id: UUID) -> dict:
        return {
            "items": [{
                "portfolio_id": "20000000-0000-0000-0000-000000000001",
                "person_id": str(person_id),
                "display_name": "Core",
                "created_at": "2026-03-01T00:00:00+00:00",
                "updated_at": "2026-03-01T00:00:00+00:00",
            }],
            "total": 1,
        }

    async def create_portfolio(self, person_id: UUID, payload) -> dict:
        return {
            "portfolio_id": "20000000-0000-0000-0000-000000000009",
            "person_id": str(person_id),
            "display_name": payload.display_name,
            "created_at": "2026-03-01T00:00:00+00:00",
            "updated_at": "2026-03-01T00:00:00+00:00",
        }

    async def get_portfolio(self, portfolio_id: UUID) -> dict:
        return {
            "portfolio_id": str(portfolio_id),
            "person_id": str(PERSON_ID),
            "display_name": "Core",
            "created_at": "2026-03-01T00:00:00+00:00",
            "updated_at": "2026-03-01T00:00:00+00:00",
            "holdings": [],
        }

    async def create_holding(self, portfolio_id: UUID, payload) -> dict:
        return {
            "holding_id": "30000000-0000-0000-0000-000000000001",
            "portfolio_id": str(portfolio_id),
            **payload.model_dump(),
            "created_at": "2026-03-01T00:00:00+00:00",
            "updated_at": "2026-03-01T00:00:00+00:00",
        }

    async def update_holding(self, portfolio_id: UUID, holding_id: UUID, payload) -> dict:
        return {
            "holding_id": str(holding_id),
            "portfolio_id": str(portfolio_id),
            "symbol": "AAPL",
            "quantity": payload.quantity or 1,
            "acquisition_price": payload.acquisition_price or 10,
            "currency": payload.currency or "EUR",
            "buy_date": payload.buy_date or "2026-03-01",
            "created_at": "2026-03-01T00:00:00+00:00",
            "updated_at": "2026-03-02T00:00:00+00:00",
        }

    async def delete_holding(self, portfolio_id: UUID, holding_id: UUID) -> None:
        return None

    async def refresh_holdings_prices(self, portfolio_id: UUID) -> dict:
        return {
            "portfolio_id": str(portfolio_id),
            "status": "not_implemented_yet",
            "accepted": False,
            "detail": "Technischer Refresh-Flow vorbereitet. Marktpreislogik folgt in einem späteren Schritt.",
        }

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

    async def search_marketdata_instruments(self, *, q: str, limit: int | None = None) -> dict:
        return {"items": [{"symbol": "AAPL", "name": "Apple Inc."}], "query": q, "limit": limit or 20}

    async def get_marketdata_summary(self, symbol: str) -> dict:
        return {"symbol": symbol, "name": "Apple Inc.", "currency": "USD"}

    async def get_marketdata_blocks(self, symbol: str) -> dict:
        return {"symbol": symbol, "blocks": {"quote": {"price": 100.0}}}

    async def get_marketdata_prices(
        self, symbol: str, *, range_value: str | None = None, interval: str | None = None
    ) -> dict:
        return {
            "symbol": symbol,
            "range": range_value or "1mo",
            "interval": interval or "1d",
            "points": [{"timestamp": "2026-03-01T00:00:00Z", "close": 100.0}],
        }

    async def get_marketdata_full(self, symbol: str) -> dict:
        return {"symbol": symbol, "summary": {"name": "Apple Inc."}, "prices": {"points": []}}

    async def get_marketdata_history(self, symbol: str, *, range_value: str | None = None) -> dict:
        return {
            "symbol": symbol,
            "range": range_value or "3m",
            "points": [{"date": "2026-03-01", "close": 100.0}],
            "cache_present": True,
            "updated_at": "2026-04-08T12:34:56Z",
        }

    async def get_marketdata_profile(self, symbol: str) -> dict:
        return {
            "symbol": symbol,
            "company_name": "Apple Inc.",
            "price": 100.0,
            "currency": "USD",
            "address_line": "One Apple Park Way, 95014 Cupertino",
        }

    async def refresh_marketdata_price(self, symbol: str) -> dict:
        return {
            "symbol": symbol,
            "trade_date": "2026-04-03",
            "current_price": 31.48,
            "price_source": "cache_today",
            "price_cache_hit": True,
            "history_cache_present": True,
            "history_action": "enrich_in_background",
            "fetched_at": "2026-04-03T12:34:56Z",
        }

    async def get_marketdata_holdings_summary(self, symbols: str) -> dict:
        return {"requested_symbols": symbols.split(","), "items": [], "total": 0, "meta": {"warnings": []}}

    async def get_marketdata_batch_prices(self, symbols: str) -> dict:
        return {"requested_symbols": symbols.split(","), "items": [{"symbol": "AAPL", "cache_status": "fresh_cache"}], "total": 1, "meta": {"warnings": [], "errors": []}}

    async def get_marketdata_batch_history(self, symbols: str, *, range_value: str | None = None) -> dict:
        return {"requested_symbols": symbols.split(","), "items": [{"symbol": "AAPL", "range": range_value or "3m", "cache_status": "fresh_cache", "points": []}], "total": 1, "meta": {"warnings": [], "errors": []}}

    async def get_marketdata_snapshot(self, symbol: str) -> dict:
        return {"symbol": symbol, "coverage": "profile+price"}

    async def get_marketdata_fundamentals(self, symbol: str) -> dict:
        return {"symbol": symbol, "company_name": "Apple Inc."}

    async def get_marketdata_metrics(self, symbol: str) -> dict:
        return {"symbol": symbol, "beta": 1.0}

    async def get_marketdata_financials(self, symbol: str, period: str | None = None) -> dict:
        return {"symbol": symbol, "period": period or "annual", "statements": {}}

    async def get_marketdata_risk(self, symbol: str, benchmark: str | None = None) -> dict:
        return {"symbol": symbol, "benchmark": benchmark or "SPY"}

    async def get_marketdata_benchmark(self, symbol: str, benchmark: str | None = None) -> dict:
        return {"symbol": symbol, "benchmark": benchmark or "SPY", "comparison": {}}

    async def get_marketdata_timeseries(self, symbol: str, series: str | None = None, benchmark: str | None = None) -> dict:
        return {"symbol": symbol, "series": series or "close", "benchmark": benchmark or "SPY"}

    async def get_marketdata_comparison_timeseries(self, symbol: str, symbols: str) -> dict:
        return {"base_symbol": symbol, "symbols": symbols.split(",")}

    async def get_marketdata_benchmark_catalog(self) -> dict:
        return {"items": [{"symbol": "SPY", "name": "SPDR S&P 500 ETF"}], "source": "stub"}

    async def search_marketdata_benchmark(self, query: str) -> dict:
        return {"query": query, "items": [{"symbol": "SPY", "name": "SPDR S&P 500 ETF"}], "total": 1}


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

    assert client.get(f"/api/v1/app/persons/{PERSON_ID}/banks").status_code == 200
    assert (
        client.post(f"/api/v1/app/persons/{PERSON_ID}/banks/30000000-0000-0000-0000-000000000001").status_code
        == 201
    )
    assert (
        client.delete(f"/api/v1/app/persons/{PERSON_ID}/banks/30000000-0000-0000-0000-000000000001").status_code
        == 204
    )

    assert client.get("/api/v1/app/banks").status_code == 200
    assert client.post(
        "/api/v1/app/banks",
        json={"name": "Neue Bank", "bic": "DEUTDEFFXXX", "blz": "12345678", "country_code": "DE"},
    ).status_code == 201

    assert client.get(f"/api/v1/app/persons/{PERSON_ID}/allowances").status_code == 200
    assert client.get(f"/api/v1/app/persons/{PERSON_ID}/allowances", params={"tax_year": 2025}).status_code == 200
    assert (
        client.put(
            f"/api/v1/app/persons/{PERSON_ID}/allowances/30000000-0000-0000-0000-000000000001",
            json={"tax_year": 2025, "amount": "125.00", "currency": "EUR"},
        ).status_code
        == 200
    )
    assert client.get(f"/api/v1/app/persons/{PERSON_ID}/allowances/summary", params={"tax_year": 2025}).status_code == 200

    assert client.get(f"/api/v1/app/persons/{PERSON_ID}/dashboard").status_code == 200
    assert client.get(f"/api/v1/app/persons/{PERSON_ID}/accounts").status_code == 200
    assert (
        client.get(f"/api/v1/app/persons/{PERSON_ID}/accounts/10000000-0000-0000-0000-000000000001").status_code == 200
    )
    assert (
        client.post(
            f"/api/v1/app/persons/{PERSON_ID}/accounts",
            json={
                "bank_id": "30000000-0000-0000-0000-000000000001",
                "account_type": "girokonto",
                "label": "Giro",
                "balance": "1200.00",
                "currency": "EUR",
            },
        ).status_code
        == 201
    )
    assert client.get("/api/v1/app/marketdata/instruments/search", params={"q": "apple", "limit": 5}).status_code == 200
    assert client.get("/api/v1/app/marketdata/instruments/AAPL/summary").status_code == 200
    assert client.get("/api/v1/app/marketdata/instruments/AAPL/blocks").status_code == 200
    assert (
        client.get(
            "/api/v1/app/marketdata/instruments/AAPL/prices",
            params={"range": "1mo", "interval": "1d"},
        ).status_code
        == 200
    )
    assert client.get("/api/v1/app/marketdata/instruments/AAPL/history", params={"range": "6m"}).status_code == 200
    assert client.get("/api/v1/app/marketdata/instruments/AAPL/full").status_code == 200
    assert client.get("/api/v1/app/marketdata/instruments/AAPL/snapshot").status_code == 200
    assert client.get("/api/v1/app/marketdata/instruments/AAPL/profile").status_code == 200
    assert client.get("/api/v1/app/marketdata/instruments/AAPL/fundamentals").status_code == 200
    assert client.get("/api/v1/app/marketdata/instruments/AAPL/metrics").status_code == 200
    assert client.get("/api/v1/app/marketdata/instruments/AAPL/financials", params={"period": "annual"}).status_code == 200
    assert client.get("/api/v1/app/marketdata/instruments/AAPL/risk", params={"benchmark": "SPY"}).status_code == 200
    assert client.get("/api/v1/app/marketdata/instruments/AAPL/benchmark", params={"benchmark": "SPY"}).status_code == 200
    assert client.get("/api/v1/app/marketdata/instruments/AAPL/timeseries", params={"series": "close", "benchmark": "SPY"}).status_code == 200
    assert client.get("/api/v1/app/marketdata/instruments/AAPL/comparison-timeseries", params={"symbols": "MSFT,NVDA"}).status_code == 200
    assert client.get("/api/v1/app/marketdata/depot/holdings-summary", params={"symbols": "AAPL,MSFT"}).status_code == 200
    assert client.get("/api/v1/app/marketdata/batch/prices", params={"symbols": "AAPL,MSFT"}).status_code == 200
    assert client.get("/api/v1/app/marketdata/batch/history", params={"symbols": "AAPL,MSFT", "range": "3m"}).status_code == 200
    assert client.get("/api/v1/app/marketdata/benchmark-catalog").status_code == 200
    assert client.get("/api/v1/app/marketdata/benchmark-search", params={"q": "sp"}).status_code == 200
    assert client.post("/api/v1/app/marketdata/instruments/AAPL/refresh-price").status_code == 200
    assert (
        client.patch(
            f"/api/v1/app/persons/{PERSON_ID}/accounts/10000000-0000-0000-0000-000000000001",
            json={"label": "Depot aktualisiert"},
        ).status_code
        == 200
    )
    assert (
        client.delete(
            f"/api/v1/app/persons/{PERSON_ID}/accounts/10000000-0000-0000-0000-000000000001"
        ).status_code
        == 204
    )
    assert client.get(f"/api/v1/app/persons/{PERSON_ID}/portfolios").status_code == 200
    assert client.post(
        "/api/v1/app/portfolios/20000000-0000-0000-0000-000000000001/holdings/refresh-current-prices"
    ).status_code == 200
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


def test_person_bank_assignment_errors_are_forwarded() -> None:
    app.dependency_overrides[get_gateway_service] = lambda: StubGatewayService()
    client = create_test_client(app)

    response = client.post(
        f"/api/v1/app/persons/{PERSON_ID}/banks/30000000-0000-0000-0000-000000000999",
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Zuordnung bereits vorhanden"
    app.dependency_overrides.clear()


def test_allowance_errors_are_forwarded() -> None:
    app.dependency_overrides[get_gateway_service] = lambda: StubGatewayService()
    client = create_test_client(app)

    response = client.put(
        f"/api/v1/app/persons/{PERSON_ID}/allowances/30000000-0000-0000-0000-000000000999",
        json={"tax_year": 2025, "amount": "100.00"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Nur für zugeordnete Banken zulässig"
    app.dependency_overrides.clear()


def test_gateway_dependency_health_endpoint() -> None:
    app.dependency_overrides[get_gateway_service] = lambda: StubGatewayService()
    client = create_test_client(app)

    response = client.get(f"/api/v1/app/persons/{PERSON_ID}/health")

    assert response.status_code == 200
    assert response.json()["data"]["dependencies"][0]["service"] == "analytics-service"
    app.dependency_overrides.clear()


def test_marketdata_routes_return_downstream_payloads() -> None:
    app.dependency_overrides[get_gateway_service] = lambda: StubGatewayService()
    client = create_test_client(app)

    search_response = client.get("/api/v1/app/marketdata/instruments/search", params={"q": "apple", "limit": 5})
    summary_response = client.get("/api/v1/app/marketdata/instruments/AAPL/summary")
    prices_response = client.get(
        "/api/v1/app/marketdata/instruments/AAPL/prices",
        params={"range": "1mo", "interval": "1d"},
    )
    history_response = client.get(
        "/api/v1/app/marketdata/instruments/AAPL/history",
        params={"range": "6m"},
    )
    profile_response = client.get("/api/v1/app/marketdata/instruments/AAPL/profile")
    refresh_response = client.post("/api/v1/app/marketdata/instruments/AAPL/refresh-price")

    assert search_response.status_code == 200
    assert search_response.json()["data"]["items"][0]["symbol"] == "AAPL"
    assert summary_response.status_code == 200
    assert summary_response.json()["data"]["symbol"] == "AAPL"
    assert prices_response.status_code == 200
    assert prices_response.json()["data"]["symbol"] == "AAPL"
    assert history_response.status_code == 200
    assert history_response.json()["data"]["range"] == "6m"
    assert history_response.json()["data"]["cache_present"] is True
    assert profile_response.status_code == 200
    assert profile_response.json()["data"]["price"] == 100.0
    assert "quote" not in profile_response.json()["data"]
    assert refresh_response.status_code == 200
    assert refresh_response.json()["data"]["history_action"] == "enrich_in_background"
    app.dependency_overrides.clear()


def test_marketdata_selection_route_is_deprecated_alias_for_profile() -> None:
    app.dependency_overrides[get_gateway_service] = lambda: StubGatewayService()
    client = create_test_client(app)

    response = client.get("/api/v1/app/marketdata/instruments/AAPL/selection")

    assert response.status_code == 200
    assert response.json()["data"]["price"] == 100.0
    app.dependency_overrides.clear()


def test_marketdata_404_is_forwarded() -> None:
    class NotFoundMarketdataStub(StubGatewayService):
        async def get_marketdata_profile(self, symbol: str) -> dict:
            raise HTTPException(status_code=404, detail="Instrument nicht gefunden")

    app.dependency_overrides[get_gateway_service] = lambda: NotFoundMarketdataStub()
    client = create_test_client(app)

    response = client.get("/api/v1/app/marketdata/instruments/UNKNOWN/profile")

    assert response.status_code == 404
    assert response.json()["detail"] == "Instrument nicht gefunden"
    app.dependency_overrides.clear()


def test_marketdata_history_500_is_forwarded() -> None:
    class FailingHistoryMarketdataStub(StubGatewayService):
        async def get_marketdata_history(self, symbol: str, *, range_value: str | None = None) -> dict:
            raise HTTPException(status_code=500, detail="Upstream Fehler")

    app.dependency_overrides[get_gateway_service] = lambda: FailingHistoryMarketdataStub()
    client = create_test_client(app)

    response = client.get("/api/v1/app/marketdata/instruments/AAPL/history", params={"range": "6m"})

    assert response.status_code == 500
    assert response.json()["detail"] == "Upstream Fehler"
    app.dependency_overrides.clear()


def test_marketdata_history_range_is_validated() -> None:
    app.dependency_overrides[get_gateway_service] = lambda: StubGatewayService()
    client = create_test_client(app)

    response = client.get("/api/v1/app/marketdata/instruments/AAPL/history", params={"range": "2m"})

    assert response.status_code == 422
    app.dependency_overrides.clear()


def test_marketdata_502_is_forwarded_when_downstream_unreachable() -> None:
    class DownstreamUnavailableMarketdataStub(StubGatewayService):
        async def get_marketdata_profile(self, symbol: str) -> dict:
            raise HTTPException(
                status_code=502,
                detail="Marketdata-Service ist derzeit nicht erreichbar. Bitte später erneut versuchen.",
            )

    app.dependency_overrides[get_gateway_service] = lambda: DownstreamUnavailableMarketdataStub()
    client = create_test_client(app)

    response = client.get("/api/v1/app/marketdata/instruments/AAPL/profile")

    assert response.status_code == 502
    assert response.json()["detail"] == "Marketdata-Service ist derzeit nicht erreichbar. Bitte später erneut versuchen."


def test_marketdata_search_limit_matches_backend_contract() -> None:
    client = create_test_client(app)

    response = client.get("/api/v1/app/marketdata/instruments/search", params={"q": "apple", "limit": 26})

    assert response.status_code == 422
    app.dependency_overrides.clear()


def test_marketdata_refresh_price_502_is_forwarded_when_downstream_unreachable() -> None:
    class DownstreamUnavailableMarketdataStub(StubGatewayService):
        async def refresh_marketdata_price(self, symbol: str) -> dict:
            raise HTTPException(
                status_code=502,
                detail="Marketdata-Service ist derzeit nicht erreichbar. Bitte später erneut versuchen.",
            )

    app.dependency_overrides[get_gateway_service] = lambda: DownstreamUnavailableMarketdataStub()
    client = create_test_client(app)

    response = client.post("/api/v1/app/marketdata/instruments/AAPL/refresh-price")

    assert response.status_code == 502
    assert response.json()["detail"] == "Marketdata-Service ist derzeit nicht erreichbar. Bitte später erneut versuchen."
    app.dependency_overrides.clear()
