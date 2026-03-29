from __future__ import annotations

from finanzuebersicht_shared.models import HealthResponse
from finanzuebersicht_shared.time_utils import utc_now


def build_health_response(*, service: str, version: str, status: str = "ok") -> HealthResponse:
    return HealthResponse(status=status, service=service, version=version, timestamp=utc_now())
