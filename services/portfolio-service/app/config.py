from __future__ import annotations

from functools import lru_cache
from urllib.parse import quote_plus

from finanzuebersicht_shared.config import ServiceSettings
from pydantic import Field


class Settings(ServiceSettings):
    app_name: str = "portfolio-service"
    portfolio_repository_backend: str = Field(default="mongo", alias="PORTFOLIO_REPOSITORY_BACKEND")

    mongo_uri: str | None = Field(default=None, alias="MONGO_URI")
    mongo_host: str = Field(default="localhost", alias="MONGO_HOST")
    mongo_port: int = Field(default=27017, alias="MONGO_PORT")
    mongo_database: str = Field(default="finanzuebersicht", alias="MONGO_DATABASE")
    mongo_user: str | None = Field(default=None, alias="MONGO_USER")
    mongo_password: str | None = Field(default=None, alias="MONGO_PASSWORD")
    mongo_auth_source: str = Field(default="admin", alias="MONGO_AUTH_SOURCE")
    mongo_portfolios_collection: str = Field(default="portfolios", alias="MONGO_PORTFOLIOS_COLLECTION")
    mongo_holdings_collection: str = Field(default="holdings", alias="MONGO_HOLDINGS_COLLECTION")
    mongo_benchmark_configs_collection: str = Field(default="benchmark_configs", alias="MONGO_BENCHMARK_CONFIGS_COLLECTION")
    portfolio_mongo_server_selection_timeout_ms: int = Field(
        default=2000, alias="PORTFOLIO_MONGO_SERVER_SELECTION_TIMEOUT_MS"
    )

    def resolved_mongo_uri(self) -> str:
        if self.mongo_uri and self.mongo_uri.strip():
            return self.mongo_uri.strip()

        host_part = f"{self.mongo_host}:{self.mongo_port}"
        if self.mongo_user and self.mongo_password:
            user = quote_plus(self.mongo_user)
            password = quote_plus(self.mongo_password)
            return f"mongodb://{user}:{password}@{host_part}/{self.mongo_database}?authSource={self.mongo_auth_source}"
        return f"mongodb://{host_part}/{self.mongo_database}"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
