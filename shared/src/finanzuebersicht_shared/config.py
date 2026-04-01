from __future__ import annotations

import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import (
    BaseSettings,
    DotEnvSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)


def _repo_root_from_config_file() -> Path:
    return Path(__file__).resolve().parents[3]


def _read_simple_dotenv(env_file: Path) -> dict[str, str]:
    if not env_file.exists():
        return {}

    values: dict[str, str] = {}
    for line in env_file.read_text(encoding="utf-8").splitlines():
        stripped_line = line.strip()
        if not stripped_line or stripped_line.startswith("#") or "=" not in stripped_line:
            continue
        key, value = stripped_line.split("=", 1)
        parsed_key = key.strip()
        parsed_value = value.strip()
        if (
            len(parsed_value) >= 2
            and parsed_value[0] == parsed_value[-1]
            and parsed_value[0] in {"'", '"'}
        ):
            parsed_value = parsed_value[1:-1]
        values[parsed_key] = parsed_value
    return values


def _setting_env_name(field_name: str, field_info: Any) -> str:
    if isinstance(field_info.alias, str) and field_info.alias:
        return field_info.alias
    return field_name.upper()


def _render_env_value(env_name: str, value: object) -> str:
    del env_name
    if value is None:
        return "<none>"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return ",".join(value)
    return str(value)


def _mask_env_value(env_name: str, rendered_value: str) -> str:
    sensitive_fragments = ("KEY", "TOKEN", "SECRET", "PASSWORD", "PASS", "PWD")
    normalized_name = env_name.upper()
    if any(fragment in normalized_name for fragment in sensitive_fragments):
        if len(rendered_value) <= 4:
            return "****"
        return f"{rendered_value[:2]}****{rendered_value[-2:]}"
    return rendered_value


class ServiceSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    app_name: str = Field(default="service", alias="APP_NAME")
    app_env: str = Field(default="dev", alias="APP_ENV")
    app_version: str = Field(default="0.1.0", alias="APP_VERSION")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    cors_allow_origins: list[str] = Field(
        default_factory=lambda: ["http://127.0.0.1:5173", "http://localhost:5173"],
        alias="CORS_ALLOW_ORIGINS",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        service_dotenv = DotEnvSettingsSource(settings_cls, env_file=Path.cwd() / ".env")
        root_dotenv = DotEnvSettingsSource(
            settings_cls,
            env_file=_repo_root_from_config_file() / ".env",
        )
        return (
            init_settings,
            env_settings,
            service_dotenv,
            root_dotenv,
            file_secret_settings,
        )

    @field_validator("cors_allow_origins", mode="before")
    @classmethod
    def parse_cors_allow_origins(cls, value: Any) -> list[str] | Any:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache(maxsize=1)
def get_settings() -> ServiceSettings:
    return ServiceSettings()


def collect_explicit_env_overrides(settings: ServiceSettings) -> list[tuple[str, str, str]]:
    process_env = os.environ
    service_dotenv = _read_simple_dotenv(Path.cwd() / ".env")
    root_dotenv = _read_simple_dotenv(_repo_root_from_config_file() / ".env")

    overrides: list[tuple[str, str, str]] = []
    for field_name, field_info in settings.__class__.model_fields.items():
        env_name = _setting_env_name(field_name, field_info)
        source_name: str | None = None
        if env_name in process_env:
            source_name = "process_env"
        elif env_name in service_dotenv:
            source_name = "service_dotenv"
        elif env_name in root_dotenv:
            source_name = "root_dotenv"

        if source_name is None:
            continue

        effective_value = getattr(settings, field_name)
        rendered_value = _render_env_value(env_name, effective_value)
        masked_value = _mask_env_value(env_name, rendered_value)
        overrides.append((env_name, source_name, masked_value))

    return sorted(overrides, key=lambda item: item[0])


def log_explicit_env_overrides(settings: ServiceSettings) -> None:
    logger = logging.getLogger("finanzuebersicht_shared.config")
    overrides = collect_explicit_env_overrides(settings)

    if not overrides:
        logger.info(
            "%s startup env confirmation: no explicit env overrides detected",
            settings.app_name,
        )
        return

    for env_name, source_name, masked_value in overrides:
        logger.info(
            "%s startup env loaded: name=%s source=%s value=%s",
            settings.app_name,
            env_name,
            source_name,
            masked_value,
        )
    logger.info(
        "%s startup env confirmation: recognized_overrides=%d",
        settings.app_name,
        len(overrides),
    )
