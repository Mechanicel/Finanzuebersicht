from __future__ import annotations

from functools import lru_cache
from urllib.parse import quote_plus

from pydantic import Field
from finanzuebersicht_shared.config import ServiceSettings


class Settings(ServiceSettings):
    app_name: str = "marketdata-service"
    cache_enabled: bool = True
    # yfinance remains the market-data provider (summary/prices/blocks/full/selection details).
    marketdata_provider: str = "yfinance"
    marketdata_request_timeout_seconds: float = 8.0
    marketdata_request_retries: int = 2
    marketdata_request_backoff_factor: float = 0.3
    # Instrument search provider configuration (OpenFIGI only).
    openfigi_base_url: str = "https://api.openfigi.com/v3"
    openfigi_api_key: str | None = None
    openfigi_request_timeout_seconds: float = 6.0
    openfigi_request_retries: int = 2
    openfigi_request_backoff_factor: float = 0.3
    openfigi_search_result_limit: int = 20
    openfigi_search_default_market_sec_des: str | None = None
    marketdata_cache_search_ttl_seconds: int = 60
    marketdata_cache_summary_ttl_seconds: int = 120
    marketdata_cache_price_ttl_seconds: int = 45
    marketdata_cache_series_ttl_seconds: int = 30
    marketdata_cache_benchmark_ttl_seconds: int = 900
    marketdata_cache_selection_ttl_seconds: int = 60
    marketdata_hydrated_freshness_ttl_seconds: int = 21600
    marketdata_mongo_enabled: bool = Field(default=True, alias="MARKETDATA_MONGO_ENABLED")
    marketdata_mongo_server_selection_timeout_ms: int = Field(
        default=1000,
        alias="MARKETDATA_MONGO_SERVER_SELECTION_TIMEOUT_MS",
    )
    mongo_uri: str | None = Field(default=None, alias="MONGO_URI")
    mongo_host: str = Field(default="localhost", alias="MONGO_HOST")
    mongo_port: int = Field(default=27017, alias="MONGO_PORT")
    mongo_database: str = Field(default="finanzuebersicht", alias="MONGO_DATABASE")
    mongo_user: str | None = Field(default=None, alias="MONGO_USER")
    mongo_password: str | None = Field(default=None, alias="MONGO_PASSWORD")
    mongo_auth_source: str = Field(default="admin", alias="MONGO_AUTH_SOURCE")
    marketdata_selection_cache_collection: str = Field(
        default="marketdata_selection_cache",
        alias="MARKETDATA_SELECTION_CACHE_COLLECTION",
    )
    marketdata_hydrated_collection: str = Field(
        default="marketdata_hydrated_instruments",
        alias="MARKETDATA_HYDRATED_COLLECTION",
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
