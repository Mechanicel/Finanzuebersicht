from __future__ import annotations

from functools import lru_cache

from finanzuebersicht_shared.config import ServiceSettings


class Settings(ServiceSettings):
    app_name: str = "api-gateway"
    analytics_service_url: str = "http://localhost:8006"
    person_service_url: str = "http://localhost:8002"
    masterdata_service_url: str = "http://localhost:8001"
    portfolio_service_url: str = "http://localhost:8004"
    account_service_url: str = "http://localhost:8003"
    marketdata_service_url: str = "http://localhost:8005"

    # 5.1 / 5.3: shortened timeout reduces cascade latency; circuit breaker
    # catches persistent failures before they drain the thread pool.
    request_timeout_seconds: float = 10.0
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_recovery_timeout_seconds: float = 30.0


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
