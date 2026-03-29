from __future__ import annotations

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import Field

from finanzuebersicht_shared.base_models import SharedModel


class ErrorDetail(SharedModel):
    code: str
    message: str
    field: str | None = None


class ErrorResponse(SharedModel):
    error: str
    request_id: str | None = None
    details: list[ErrorDetail] = Field(default_factory=list)


class HealthResponse(SharedModel):
    status: str
    service: str
    version: str
    timestamp: datetime


T = TypeVar("T")


class ApiResponse(SharedModel, Generic[T]):
    data: T
    request_id: str | None = None
    correlation_id: str | None = None
