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


def test_health_endpoint() -> None:
    client = create_test_client(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert_standard_health_payload(response.json(), "marketdata-service")


def test_ready_endpoint() -> None:
    client = create_test_client(app)
    response = client.get("/ready")

    assert response.status_code == 200
    assert_standard_health_payload(response.json(), "marketdata-service")


def test_api_v1_prefix_and_request_ids() -> None:
    client = create_test_client(app)
    response = client.get("/api/v1/marketdata_service")

    assert response.status_code == 200
    assert response.headers["X-Request-ID"]
    assert response.headers["X-Correlation-ID"]
    body = response.json()
    assert body["data"]["service"] == "marketdata-service"
