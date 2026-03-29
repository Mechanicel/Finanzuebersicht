from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from finanzuebersicht_shared.models import ErrorDetail, ErrorResponse


def _validation_details(exc: RequestValidationError) -> list[ErrorDetail]:
    return [
        ErrorDetail(code=err["type"], message=err["msg"], field=".".join(map(str, err["loc"])))
        for err in exc.errors()
    ]


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        payload = ErrorResponse(
            error="validation_error",
            request_id=getattr(request.state, "request_id", None),
            details=_validation_details(exc),
        )
        return JSONResponse(status_code=422, content=payload.model_dump())

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        payload = ErrorResponse(
            error="internal_server_error",
            request_id=getattr(request.state, "request_id", None),
            details=[ErrorDetail(code="internal_error", message=str(exc))],
        )
        return JSONResponse(status_code=500, content=payload.model_dump())
