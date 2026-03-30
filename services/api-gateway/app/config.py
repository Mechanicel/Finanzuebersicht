from __future__ import annotations

from functools import lru_cache

from finanzuebersicht_shared.config import ServiceSettings


class Settings(ServiceSettings):
    app_name: str = "api-gateway"
    analytics_service_url: str = "http://localhost:8006"
    person_service_url: str = "http://localhost:8002"
    masterdata_service_url: str = "http://localhost:8005"
    portfolio_service_url: str = "http://localhost:8004"
    account_service_url: str = "http://localhost:8003"
    request_timeout_seconds: float = 3.0


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
