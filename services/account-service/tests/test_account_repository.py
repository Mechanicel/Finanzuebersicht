# ruff: noqa: E402
from __future__ import annotations

import sys
from pathlib import Path
from uuid import UUID

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
from app.dependencies import get_mongo_client, get_mongo_database, get_repository
from app.models import AccountType, PersonAccount
from app.repositories import InMemoryAccountRepository, MongoAccountRepository


def _account(*, account_id: str, person_id: str, label: str, created_at: str) -> PersonAccount:
    return PersonAccount(
        account_id=UUID(account_id),
        person_id=UUID(person_id),
        bank_id=UUID("30000000-0000-0000-0000-000000000001"),
        account_type=AccountType.DEPOT,
        label=label,
        balance="100.00",
        currency="EUR",
        created_at=created_at,
        updated_at=created_at,
    )


def test_mongo_repository_persists_across_instances() -> None:
    client = mongomock.MongoClient()
    database = client["finanzuebersicht"]
    repo_a = MongoAccountRepository(database, account_collection="accounts")
    person_id = UUID("00000000-0000-0000-0000-000000000101")
    account_id = UUID("10000000-0000-0000-0000-000000000001")

    created = _account(
        account_id=str(account_id),
        person_id=str(person_id),
        label="Depot A",
        created_at="2026-01-01T00:00:00+00:00",
    )
    repo_a.create_person_account(created)

    repo_b = MongoAccountRepository(database, account_collection="accounts")
    accounts = repo_b.list_person_accounts(person_id)
    assert len(accounts) == 1
    assert accounts[0].account_id == account_id

    loaded = repo_b.get_person_account(person_id, account_id)
    assert loaded is not None
    assert loaded.label == "Depot A"


def test_mongo_repository_update_and_sort_order() -> None:
    client = mongomock.MongoClient()
    database = client["finanzuebersicht"]
    repository = MongoAccountRepository(database, account_collection="accounts")
    person_id = UUID("00000000-0000-0000-0000-000000000101")

    newer = _account(
        account_id="10000000-0000-0000-0000-000000000002",
        person_id=str(person_id),
        label="Neu",
        created_at="2026-01-02T00:00:00+00:00",
    )
    older = _account(
        account_id="10000000-0000-0000-0000-000000000003",
        person_id=str(person_id),
        label="Alt",
        created_at="2026-01-01T00:00:00+00:00",
    )
    repository.create_person_account(newer)
    repository.create_person_account(older)

    sorted_accounts = repository.list_person_accounts(person_id)
    assert [item.label for item in sorted_accounts] == ["Alt", "Neu"]

    updated = newer.model_copy(
        update={"label": "Neu Aktualisiert", "updated_at": "2026-01-03T00:00:00+00:00"}
    )
    repository.update_person_account(updated)

    reloaded = repository.get_person_account(person_id, newer.account_id)
    assert reloaded is not None
    assert reloaded.label == "Neu Aktualisiert"
    assert reloaded.updated_at == "2026-01-03T00:00:00+00:00"


def test_inmemory_repository_still_supported() -> None:
    repository = InMemoryAccountRepository()
    person_id = UUID("00000000-0000-0000-0000-000000000101")
    account = _account(
        account_id="10000000-0000-0000-0000-000000000004",
        person_id=str(person_id),
        label="Fallback",
        created_at="2026-01-01T00:00:00+00:00",
    )

    repository.create_person_account(account)
    loaded = repository.get_person_account(person_id, account.account_id)

    assert loaded is not None
    assert loaded.label == "Fallback"


@pytest.mark.parametrize(
    ("backend", "expected_type"),
    [
        ("inmemory", InMemoryAccountRepository),
        ("mongo", MongoAccountRepository),
    ],
)
def test_repository_backend_selection(
    monkeypatch: pytest.MonkeyPatch,
    backend: str,
    expected_type: type[InMemoryAccountRepository] | type[MongoAccountRepository],
) -> None:
    monkeypatch.setenv("ACCOUNT_REPOSITORY_BACKEND", backend)
    monkeypatch.setattr(account_dependencies, "MongoClient", mongomock.MongoClient)

    get_repository.cache_clear()
    get_mongo_database.cache_clear()
    get_mongo_client.cache_clear()
    get_settings.cache_clear()

    repository = get_repository()
    assert isinstance(repository, expected_type)


def test_repository_delete_account() -> None:
    repository = InMemoryAccountRepository()
    person_id = UUID("00000000-0000-0000-0000-000000000101")
    account = _account(
        account_id="10000000-0000-0000-0000-000000000005",
        person_id=str(person_id),
        label="Delete Me",
        created_at="2026-01-01T00:00:00+00:00",
    )

    repository.create_person_account(account)
    assert repository.delete_person_account(person_id, account.account_id) is True
    assert repository.get_person_account(person_id, account.account_id) is None
