from __future__ import annotations

import logging
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import quote_plus

from dotenv import load_dotenv

logger = logging.getLogger(__name__)


def _discover_project_root() -> Path:
    override = os.getenv("FINANZUEBERSICHT_ROOT", "").strip()
    if override:
        return Path(override).expanduser().resolve()

    current_file = Path(__file__).resolve()
    markers = (".env.example", "FrontendService", "markedataservice")

    for candidate in current_file.parents:
        if all((candidate / marker).exists() for marker in markers):
            return candidate

    return Path.cwd().resolve()


PROJECT_ROOT = _discover_project_root()
ENV_FILE = PROJECT_ROOT / ".env"
ENV_EXAMPLE_FILE = PROJECT_ROOT / ".env.example"


def ensure_local_env_file() -> None:
    """Erzeugt eine lokale .env auf Basis der .env.example, falls sie fehlt."""
    if ENV_FILE.exists() or not ENV_EXAMPLE_FILE.exists():
        return
    ENV_FILE.write_text(ENV_EXAMPLE_FILE.read_text(encoding="utf-8"), encoding="utf-8")
    logger.info(".env wurde aus .env.example erzeugt")


@dataclass(frozen=True)
class Settings:
    mongo_uri: str
    mongo_host: str
    mongo_port: int
    mongo_username: str
    mongo_password: str
    mongo_auth_source: str
    mongo_db_name: str
    mongo_person_collection: str
    mongo_bank_collection: str
    mongo_account_type_collection: str
    mongo_marketdata_collection: str
    frontend_seed_personen_file: Path
    frontend_seed_banken_file: Path
    frontend_seed_kontotypen_file: Path
    marketdata_base_url: str
    marketdata_host: str
    marketdata_port: int
    log_verbosity: str
    performance_logging: bool

    @property
    def mongo_collections(self) -> Iterable[str]:
        return (
            self.mongo_person_collection,
            self.mongo_bank_collection,
            self.mongo_account_type_collection,
            self.mongo_marketdata_collection,
        )


def _build_mongo_uri(
    mongo_uri_override: str,
    host: str,
    port: int,
    db_name: str,
    username: str,
    password: str,
    auth_source: str,
) -> str:
    if mongo_uri_override:
        return mongo_uri_override

    credentials = ""
    if username:
        encoded_user = quote_plus(username)
        encoded_password = quote_plus(password)
        credentials = f"{encoded_user}:{encoded_password}@"

    return f"mongodb://{credentials}{host}:{port}/{db_name}?authSource={quote_plus(auth_source)}"


def normalize_log_verbosity(value: str) -> str:
    normalized = value.strip().lower()
    if normalized in {"error", "debug", "trace"}:
        return normalized
    return "debug"


def parse_bool_env(value: str, default: bool = False) -> bool:
    normalized = (value or "").strip().lower()
    if not normalized:
        return default
    return normalized in {"1", "true", "yes", "on"}


def get_settings() -> Settings:
    ensure_local_env_file()
    load_dotenv(ENV_FILE)

    def env(name: str, default: str) -> str:
        return os.getenv(name, default).strip()

    mongo_host = env("MONGO_HOST", "localhost")
    mongo_port = int(env("MONGO_PORT", "27017"))
    mongo_db_name = env("MONGO_DB_NAME", "finanzuebersicht")
    mongo_username = env("MONGO_USERNAME", "")
    mongo_password = env("MONGO_PASSWORD", "")
    mongo_auth_source = env("MONGO_AUTH_SOURCE", "admin")
    mongo_uri_override = env("MONGO_URI", "")

    settings = Settings(
        mongo_uri=_build_mongo_uri(
            mongo_uri_override=mongo_uri_override,
            host=mongo_host,
            port=mongo_port,
            db_name=mongo_db_name,
            username=mongo_username,
            password=mongo_password,
            auth_source=mongo_auth_source,
        ),
        mongo_host=mongo_host,
        mongo_port=mongo_port,
        mongo_username=mongo_username,
        mongo_password=mongo_password,
        mongo_auth_source=mongo_auth_source,
        mongo_db_name=mongo_db_name,
        mongo_person_collection=env("MONGO_PERSON_COLLECTION", "personen"),
        mongo_bank_collection=env("MONGO_BANK_COLLECTION", "banken"),
        mongo_account_type_collection=env("MONGO_ACCOUNT_TYPE_COLLECTION", "kontotypen"),
        mongo_marketdata_collection=env("MONGO_MARKETDATA_COLLECTION", "marketdata_cache"),
        frontend_seed_personen_file=PROJECT_ROOT / env("FRONTEND_SEED_PERSONEN_FILE", "FrontendService/seeds/personen.json"),
        frontend_seed_banken_file=PROJECT_ROOT / env("FRONTEND_SEED_BANKEN_FILE", "FrontendService/seeds/banken.json"),
        frontend_seed_kontotypen_file=PROJECT_ROOT
        / env("FRONTEND_SEED_KONTOTYPEN_FILE", "FrontendService/seeds/kontotypen.json"),
        marketdata_base_url=env("MARKETDATA_BASE_URL", "http://127.0.0.1:5000"),
        marketdata_host=env("MARKETDATA_HOST", "0.0.0.0"),
        marketdata_port=int(env("MARKETDATA_PORT", "5000")),
        log_verbosity=normalize_log_verbosity(env("LOG_VERBOSITY", "debug")),
        performance_logging=parse_bool_env(env("PERFORMANCE_LOGGING", "false"), default=False),
    )
    return settings


def docker_compose_command() -> list[str]:
    if shutil.which("docker"):
        return ["docker", "compose"]
    if shutil.which("docker-compose"):
        return ["docker-compose"]
    return []
