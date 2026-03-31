# ruff: noqa: E402
from __future__ import annotations

import sys
from pathlib import Path

import mongomock
import pytest

ROOT = Path(__file__).resolve().parents[3]
SHARED_SRC = ROOT / "shared" / "src"
if str(SHARED_SRC) not in sys.path:
    sys.path.insert(0, str(SHARED_SRC))

SERVICE_ROOT = Path(__file__).resolve().parents[1]
if "app" in sys.modules:
    del sys.modules["app"]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

import app.dependencies as account_dependencies
from app.config import get_settings
from app.dependencies import (
    get_account_service,
    get_mongo_client,
    get_mongo_database,
    get_repository,
)


@pytest.fixture(autouse=True)
def default_test_repository(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ACCOUNT_REPOSITORY_BACKEND", "mongo")
    monkeypatch.setattr(account_dependencies, "MongoClient", mongomock.MongoClient)

    get_account_service.cache_clear()
    get_repository.cache_clear()
    get_mongo_database.cache_clear()
    get_mongo_client.cache_clear()
    get_settings.cache_clear()
