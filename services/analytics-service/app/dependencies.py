from __future__ import annotations

from functools import lru_cache

from app.config import get_settings
from app.service import AnalyticsService


@lru_cache(maxsize=1)
def get_analytics_service() -> AnalyticsService:
    settings = get_settings()
    return AnalyticsService(
        person_base_url=settings.person_service_url,
        account_base_url=settings.account_service_url,
        portfolio_base_url=settings.portfolio_service_url,
        marketdata_base_url=settings.marketdata_service_url,
        timeout_seconds=settings.request_timeout_seconds,
        dashboard_cache_ttl_seconds=settings.dashboard_cache_ttl_seconds,
    )
