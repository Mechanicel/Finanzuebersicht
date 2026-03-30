from __future__ import annotations

from functools import lru_cache
from urllib.parse import quote_plus

from finanzuebersicht_shared.config import ServiceSettings
from pydantic import Field


class Settings(ServiceSettings):
    app_name: str = "person-service"

    mongo_uri: str | None = Field(default=None, alias="MONGO_URI")
    mongo_host: str = Field(default="localhost", alias="MONGO_HOST")
    mongo_port: int = Field(default=27017, alias="MONGO_PORT")
    mongo_database: str = Field(default="finanzuebersicht", alias="MONGO_DATABASE")
    mongo_user: str | None = Field(default=None, alias="MONGO_USER")
    mongo_password: str | None = Field(default=None, alias="MONGO_PASSWORD")
    mongo_auth_source: str = Field(default="admin", alias="MONGO_AUTH_SOURCE")

    mongo_person_collection: str = Field(default="persons", alias="MONGO_PERSON_COLLECTION")
    mongo_assignment_collection: str = Field(
        default="person_bank_assignments", alias="MONGO_ASSIGNMENT_COLLECTION"
    )
    mongo_allowance_collection: str = Field(default="tax_allowances", alias="MONGO_ALLOWANCE_COLLECTION")

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
