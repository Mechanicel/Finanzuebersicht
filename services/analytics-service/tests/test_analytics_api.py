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

from app.main import app
from finanzuebersicht_shared.testing import assert_standard_health_payload, create_test_client

PERSON_ID = "00000000-0000-0000-0000-000000000101"


def test_health_endpoint() -> None:
    client = create_test_client(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert_standard_health_payload(response.json(), "analytics-service")


def test_overview_endpoint_is_chart_friendly() -> None:
    client = create_test_client(app)
    response = client.get(f"/api/v1/analytics/persons/{PERSON_ID}/overview")

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["labels"]
    assert payload["series"][0]["points"][0]["x"]
    assert payload["kpis"]


def test_all_analytics_endpoints_exist() -> None:
    client = create_test_client(app)
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


def test_unknown_person_returns_404() -> None:
    client = create_test_client(app)
    response = client.get("/api/v1/analytics/persons/00000000-0000-0000-0000-000000000999/overview")

    assert response.status_code == 404
