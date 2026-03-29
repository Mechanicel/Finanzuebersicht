from __future__ import annotations

from fastapi import APIRouter, Request
from finanzuebersicht_shared.models import ApiResponse

router = APIRouter(tags=["v1"])


@router.get("/person_service", response_model=ApiResponse[dict[str, str]])
async def service_info(request: Request) -> ApiResponse[dict[str, str]]:
    return ApiResponse(
        data={"service": "person-service", "message": "API v1 placeholder"},
        request_id=getattr(request.state, "request_id", None),
        correlation_id=getattr(request.state, "correlation_id", None),
    )
