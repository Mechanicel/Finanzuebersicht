from __future__ import annotations

from functools import lru_cache

from app.config import get_settings
from app.service import GatewayService


@lru_cache(maxsize=1)
def get_gateway_service() -> GatewayService:
    settings = get_settings()
    return GatewayService(
        analytics_base_url=settings.analytics_service_url,
        person_base_url=settings.person_service_url,
        timeout_seconds=settings.request_timeout_seconds,
    )
