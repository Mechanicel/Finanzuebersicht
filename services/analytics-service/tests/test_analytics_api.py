# ruff: noqa: E402
from __future__ import annotations

import sys
from pathlib import Path
from uuid import UUID

import httpx

ROOT = Path(__file__).resolve().parents[3]
SHARED_SRC = ROOT / "shared" / "src"
if str(SHARED_SRC) not in sys.path:
    sys.path.append(str(SHARED_SRC))

SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.append(str(SERVICE_ROOT))

from app.dependencies import get_analytics_service
from app.main import app
from app.service import AnalyticsService
from finanzuebersicht_shared.testing import assert_standard_health_payload, create_test_client

PERSON_ID = "00000000-0000-0000-0000-000000000101"
UNKNOWN_PERSON_ID = "00000000-0000-0000-0000-000000000999"


class FakeAnalyticsService(AnalyticsService):
    def __init__(self) -> None:
        super().__init__(
            person_base_url="http://person-service",
            account_base_url="http://account-service",
            portfolio_base_url="http://portfolio-service",
            marketdata_base_url="http://marketdata-service",
            timeout_seconds=1.0,
            dashboard_cache_ttl_seconds=120.0,
        )

    def _request_json(self, url: str, client=None) -> dict | list[dict]:
        if UNKNOWN_PERSON_ID in url:
            raise KeyError("Unknown person_id")

        if "/persons/" in url and url.endswith(PERSON_ID):
            return {
                "person": {
                    "person_id": PERSON_ID,
                    "first_name": "Max",
                    "last_name": "Mustermann",
                }
            }

        if "/accounts" in url:
            return [
                {"account_type": "girokonto", "balance": "1000.00"},
                {"account_type": "depot", "balance": "500.00"},
            ]

        if url.endswith(f"/persons/{PERSON_ID}/portfolios"):
            return {"items": [{"portfolio_id": "p-1", "display_name": "Depot"}], "total": 1}

        if url.endswith("/portfolios/p-1"):
            return {
                "holdings": [
                    {"symbol": "AAPL", "quantity": 2, "acquisition_price": 100},
                    {"symbol": "MSFT", "quantity": 1, "acquisition_price": 150},
                ]
            }

        if "/profile" in url and "AAPL" in url:
            return {"price": 110.0}
        if "/profile" in url and "MSFT" in url:
            return {"price": 140.0}

        if "/history" in url and "AAPL" in url:
            return {"points": [{"date": "2026-01-01", "close": 100}, {"date": "2026-01-02", "close": 110}]}
        if "/history" in url and "MSFT" in url:
            return {"points": [{"date": "2026-01-01", "close": 140}, {"date": "2026-01-02", "close": 145}]}

        return {}


def _client_with_fake_service():
    app.dependency_overrides[get_analytics_service] = lambda: FakeAnalyticsService()
    return create_test_client(app)


def teardown_function() -> None:
    app.dependency_overrides.clear()


def test_health_endpoint() -> None:
    client = create_test_client(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert_standard_health_payload(response.json(), "analytics-service")


def test_overview_endpoint_is_chart_friendly() -> None:
    client = _client_with_fake_service()
    response = client.get(f"/api/v1/analytics/persons/{PERSON_ID}/overview")

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["labels"]
    assert payload["series"][0]["points"][0]["x"]
    assert payload["kpis"]


def test_all_analytics_endpoints_exist() -> None:
    client = _client_with_fake_service()
    suffixes = [
        "allocation",
        "timeseries",
        "monthly-comparison",
        "metrics",
        "heatmap",
        "forecast",
    ]
    for suffix in suffixes:
        response = client.get(f"/api/v1/analytics/persons/{PERSON_ID}/{suffix}")
        assert response.status_code == 200, suffix
        assert response.json()["data"]["meta"]["loading"] is False

    dashboard_suffixes = ["overview", "allocation", "timeseries", "metrics"]
    for suffix in dashboard_suffixes:
        response = client.get(f"/api/v1/analytics/persons/{PERSON_ID}/dashboard/{suffix}")
        assert response.status_code == 200, suffix
        payload = response.json()["data"]
        assert payload["section"] == suffix
        assert payload["state"] in {"pending", "ready", "stale", "error"}


def test_unknown_person_returns_404() -> None:
    client = _client_with_fake_service()
    response = client.get(f"/api/v1/analytics/persons/{UNKNOWN_PERSON_ID}/overview")

    assert response.status_code == 404
    section_response = client.get(f"/api/v1/analytics/persons/{UNKNOWN_PERSON_ID}/dashboard/overview")
    assert section_response.status_code == 404


def test_known_person_with_empty_data_returns_stable_structure() -> None:
    class EmptyDataService(FakeAnalyticsService):
        def _request_json(self, url: str, client=None) -> dict | list[dict]:
            if "/persons/" in url and url.endswith(PERSON_ID):
                return {"person": {"person_id": PERSON_ID}}
            if "/accounts" in url:
                return []
            if url.endswith(f"/persons/{PERSON_ID}/portfolios"):
                return {"items": [], "total": 0}
            return {}

    app.dependency_overrides[get_analytics_service] = lambda: EmptyDataService()
    client = create_test_client(app)

    response = client.get(f"/api/v1/analytics/persons/{PERSON_ID}/timeseries")

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["series"][0]["points"] == []
    assert payload["summary"]["value"] == 0


def test_dashboard_deduplicates_symbol_requests() -> None:
    class DedupService(FakeAnalyticsService):
        def __init__(self) -> None:
            super().__init__()
            self.price_calls: dict[str, int] = {}
            self.history_calls: dict[str, int] = {}

        def _request_json(self, url: str, client=None) -> dict | list[dict]:
            if url.endswith(f"/persons/{PERSON_ID}/portfolios"):
                return {
                    "items": [
                        {"portfolio_id": "p-1", "display_name": "Depot 1"},
                        {"portfolio_id": "p-2", "display_name": "Depot 2"},
                    ],
                    "total": 2,
                }
            if url.endswith("/portfolios/p-1"):
                return {
                    "holdings": [
                        {"symbol": "AAPL", "quantity": 2, "acquisition_price": 100},
                        {"symbol": "MSFT", "quantity": 1, "acquisition_price": 150},
                    ]
                }
            if url.endswith("/portfolios/p-2"):
                return {
                    "holdings": [
                        {"symbol": "AAPL", "quantity": 3, "acquisition_price": 90},
                    ]
                }
            if "/profile" in url:
                symbol = url.split("/instruments/")[1].split("/")[0]
                self.price_calls[symbol] = self.price_calls.get(symbol, 0) + 1
            if "/history" in url:
                symbol = url.split("/instruments/")[1].split("/")[0]
                self.history_calls[symbol] = self.history_calls.get(symbol, 0) + 1
            return super()._request_json(url)

    service = DedupService()
    dashboard = service._dashboard_data(UUID(PERSON_ID))

    assert dashboard.holdings_count == 3
    assert service.price_calls == {"AAPL": 1, "MSFT": 1}
    assert service.history_calls == {"AAPL": 1, "MSFT": 1}


def test_dashboard_falls_back_when_marketdata_for_symbol_fails() -> None:
    class PartialFailureService(FakeAnalyticsService):
        def _request_json(self, url: str, client=None) -> dict | list[dict]:
            if "/profile" in url and "MSFT" in url:
                raise httpx.HTTPStatusError(
                    "marketdata unavailable",
                    request=httpx.Request("GET", url),
                    response=httpx.Response(503, request=httpx.Request("GET", url)),
                )
            if "/history" in url and "MSFT" in url:
                raise httpx.HTTPStatusError(
                    "history unavailable",
                    request=httpx.Request("GET", url),
                    response=httpx.Response(503, request=httpx.Request("GET", url)),
                )
            return super()._request_json(url)

    service = PartialFailureService()
    dashboard = service._dashboard_data(UUID(PERSON_ID))

    # AAPL: 2 * 110, MSFT fallback: 1 * 150 acquisition
    assert dashboard.current_value == 370.0
    assert [point.x for point in dashboard.timeseries_points] == ["2026-01-01", "2026-01-02"]
    assert [point.y for point in dashboard.timeseries_points] == [200.0, 220.0]
