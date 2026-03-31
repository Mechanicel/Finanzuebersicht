from __future__ import annotations

from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import JSONResponse
from finanzuebersicht_shared import create_app
from finanzuebersicht_shared.models import ErrorDetail, ErrorResponse

from app.config import get_settings
from app.models import BadRequestError, NotFoundError, UpstreamServiceError
from app.routers import api_v1_router


def build_api_router() -> APIRouter:
    router = APIRouter()
    router.include_router(api_v1_router)
    return router


def _register_marketdata_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(NotFoundError)
    async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
        payload = ErrorResponse(
            error="not_found",
            request_id=getattr(request.state, "request_id", None),
            details=[ErrorDetail(code="not_found", message=exc.message)],
        )
        return JSONResponse(status_code=404, content=payload.model_dump())

    @app.exception_handler(BadRequestError)
    async def bad_request_handler(request: Request, exc: BadRequestError) -> JSONResponse:
        payload = ErrorResponse(
            error="bad_request",
            request_id=getattr(request.state, "request_id", None),
            details=[ErrorDetail(code="bad_request", message=exc.message)],
        )
        return JSONResponse(status_code=400, content=payload.model_dump())

    @app.exception_handler(UpstreamServiceError)
    async def upstream_handler(request: Request, exc: UpstreamServiceError) -> JSONResponse:
        payload = ErrorResponse(
            error="upstream_unavailable",
            request_id=getattr(request.state, "request_id", None),
            details=[ErrorDetail(code="upstream_unavailable", message=exc.message)],
        )
        return JSONResponse(status_code=503, content=payload.model_dump())


def create_application() -> FastAPI:
    settings = get_settings()
    app = create_app(settings=settings, api_router=build_api_router())
    _register_marketdata_error_handlers(app)
    return app
