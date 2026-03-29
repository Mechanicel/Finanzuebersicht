from __future__ import annotations

from functools import lru_cache

from finanzuebersicht_shared.config import ServiceSettings


class Settings(ServiceSettings):
    app_name: str = "marketdata-service"
    cache_enabled: bool = True
    cache_ttl_seconds: int = 120


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
