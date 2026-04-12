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
        masterdata_base_url=settings.masterdata_service_url,
        account_base_url=settings.account_service_url,
        portfolio_base_url=settings.portfolio_service_url,
        marketdata_base_url=settings.marketdata_service_url,
        timeout_seconds=settings.request_timeout_seconds,
        circuit_breaker_failure_threshold=settings.circuit_breaker_failure_threshold,
        circuit_breaker_recovery_timeout_seconds=settings.circuit_breaker_recovery_timeout_seconds,
    )
