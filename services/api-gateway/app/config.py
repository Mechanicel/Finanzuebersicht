from __future__ import annotations

from functools import lru_cache

from finanzuebersicht_shared.config import ServiceSettings


class Settings(ServiceSettings):
    app_name: str = "api-gateway"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
