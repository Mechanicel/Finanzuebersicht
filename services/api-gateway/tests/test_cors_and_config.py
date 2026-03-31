# ruff: noqa: E402
from __future__ import annotations

import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from fastapi import APIRouter

ROOT = Path(__file__).resolve().parents[3]
SHARED_SRC = ROOT / "shared" / "src"
if str(SHARED_SRC) not in sys.path:
    sys.path.append(str(SHARED_SRC))

SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.append(str(SERVICE_ROOT))

from finanzuebersicht_shared import ServiceSettings, create_app
from finanzuebersicht_shared.testing import create_test_client

_gateway_config_spec = spec_from_file_location(
    "api_gateway_config", SERVICE_ROOT / "app" / "config.py"
)
assert _gateway_config_spec is not None and _gateway_config_spec.loader is not None
_gateway_config_module = module_from_spec(_gateway_config_spec)
_gateway_config_spec.loader.exec_module(_gateway_config_module)
Settings = _gateway_config_module.Settings


def _build_router() -> APIRouter:
    router = APIRouter()

    @router.get("/app/persons")
    async def persons() -> dict:
        return {"items": []}

    return router


def test_cors_headers_on_regular_request_for_default_local_origin() -> None:
    app = create_app(settings=ServiceSettings(app_name="test-service"), api_router=_build_router())
    client = create_test_client(app)

    response = client.get("/health", headers={"Origin": "http://127.0.0.1:5173"})

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"
    assert response.headers["access-control-allow-credentials"] == "true"


def test_cors_preflight_on_api_route_returns_expected_headers() -> None:
    app = create_app(settings=ServiceSettings(app_name="test-service"), api_router=_build_router())
    client = create_test_client(app)

    response = client.options(
        "/api/v1/app/persons",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"
    assert response.headers["access-control-allow-credentials"] == "true"
    assert "GET" in response.headers["access-control-allow-methods"]


def test_default_cors_origins_include_local_vite_hosts() -> None:
    settings = ServiceSettings()
    assert "http://127.0.0.1:5173" in settings.cors_allow_origins
    assert "http://localhost:5173" in settings.cors_allow_origins


def test_api_gateway_default_person_service_port_matches_dev_script() -> None:
    settings = Settings()
    assert settings.person_service_url == "http://localhost:8002"
    assert settings.account_service_url == "http://localhost:8003"
    assert settings.marketdata_service_url == "http://localhost:8005"
