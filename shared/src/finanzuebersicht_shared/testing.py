from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient


def create_test_client(app: FastAPI) -> TestClient:
    return TestClient(app)


def assert_standard_health_payload(payload: dict, service_name: str) -> None:
    assert payload["service"] == service_name
    assert payload["status"] in {"ok", "ready"}
    assert "version" in payload
    assert "timestamp" in payload
