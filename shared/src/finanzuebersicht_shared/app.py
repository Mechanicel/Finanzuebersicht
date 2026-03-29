from __future__ import annotations

from fastapi import APIRouter, FastAPI

from finanzuebersicht_shared.config import ServiceSettings
from finanzuebersicht_shared.errors import register_error_handlers
from finanzuebersicht_shared.health import build_health_response
from finanzuebersicht_shared.logging import configure_logging
from finanzuebersicht_shared.request_context import RequestContextMiddleware


def create_app(*, settings: ServiceSettings, api_router: APIRouter | None = None) -> FastAPI:
    configure_logging(settings.log_level)

    app = FastAPI(title=settings.app_name, version=settings.app_version)
    app.add_middleware(RequestContextMiddleware)
    register_error_handlers(app)

    @app.get("/health")
    async def health() -> dict:
        return build_health_response(
            service=settings.app_name, version=settings.app_version
        ).model_dump()

    @app.get("/ready")
    async def ready() -> dict:
        return build_health_response(
            service=settings.app_name,
            version=settings.app_version,
            status="ready",
        ).model_dump()

    if api_router is not None:
        app.include_router(api_router, prefix="/api/v1")

    return app
