from __future__ import annotations

import logging
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent
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
    mongo_db_name: str
    mongo_person_collection: str
    mongo_bank_collection: str
    mongo_account_type_collection: str
    frontend_seed_personen_file: Path
    frontend_seed_banken_file: Path
    frontend_seed_kontotypen_file: Path
    marketdata_base_url: str
    marketdata_host: str
    marketdata_port: int

    @property
    def mongo_collections(self) -> Iterable[str]:
        return (
            self.mongo_person_collection,
            self.mongo_bank_collection,
            self.mongo_account_type_collection,
        )


def get_settings() -> Settings:
    ensure_local_env_file()
    load_dotenv(ENV_FILE)

    def env(name: str, default: str) -> str:
        return os.getenv(name, default).strip()

    settings = Settings(
        mongo_uri=env("MONGO_URI", "mongodb://localhost:27017"),
        mongo_db_name=env("MONGO_DB_NAME", "finanzuebersicht"),
        mongo_person_collection=env("MONGO_PERSON_COLLECTION", "personen"),
        mongo_bank_collection=env("MONGO_BANK_COLLECTION", "banken"),
        mongo_account_type_collection=env("MONGO_ACCOUNT_TYPE_COLLECTION", "kontotypen"),
        frontend_seed_personen_file=PROJECT_ROOT / env("FRONTEND_SEED_PERSONEN_FILE", "FrontendService/personen.json"),
        frontend_seed_banken_file=PROJECT_ROOT / env("FRONTEND_SEED_BANKEN_FILE", "FrontendService/src/data/banken.json"),
        frontend_seed_kontotypen_file=PROJECT_ROOT / env("FRONTEND_SEED_KONTOTYPEN_FILE", "FrontendService/src/data/kontotypen.json"),
        marketdata_base_url=env("MARKETDATA_BASE_URL", "http://127.0.0.1:5000"),
        marketdata_host=env("MARKETDATA_HOST", "0.0.0.0"),
        marketdata_port=int(env("MARKETDATA_PORT", "5000")),
    )
    return settings


def docker_compose_command() -> list[str]:
    if shutil.which("docker"):
        return ["docker", "compose"]
    if shutil.which("docker-compose"):
        return ["docker-compose"]
    return []
