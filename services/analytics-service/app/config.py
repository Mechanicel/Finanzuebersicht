from __future__ import annotations

from functools import lru_cache

from finanzuebersicht_shared.config import ServiceSettings


class Settings(ServiceSettings):
    app_name: str = "analytics-service"
    person_service_url: str = "http://localhost:8002"
    account_service_url: str = "http://localhost:8003"
    portfolio_service_url: str = "http://localhost:8004"
    marketdata_service_url: str = "http://localhost:8005"
    request_timeout_seconds: float = 3.0
    dashboard_cache_ttl_seconds: float = 45.0
    dashboard_section_refresh_workers: int = 8
    portfolio_snapshot_cache_ttl_seconds: float = 10.0


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
