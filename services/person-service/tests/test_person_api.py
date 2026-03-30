# ruff: noqa: E402
from __future__ import annotations

import sys
from pathlib import Path
from uuid import UUID, uuid4

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


from finanzuebersicht_shared.testing import assert_standard_health_payload, create_test_client

from app.dependencies import get_mongo_client, get_mongo_database, get_repository
from app.main import app


@pytest.fixture(autouse=True)
def reset_repo(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.dependencies.MongoClient", mongomock.MongoClient)
    get_repository.cache_clear()
    get_mongo_database.cache_clear()
    get_mongo_client.cache_clear()


def test_health_and_ready_endpoints() -> None:
    client = create_test_client(app)
    health = client.get("/health")
    ready = client.get("/ready")

    assert health.status_code == 200
    assert_standard_health_payload(health.json(), "person-service")
    assert ready.status_code == 200
    assert_standard_health_payload(ready.json(), "person-service")


def test_person_crud_and_list_filters() -> None:
    client = create_test_client(app)

    create_a = client.post("/api/v1/persons", json={"first_name": "Anna", "last_name": "Meyer", "email": "A@x.de"})
    create_b = client.post("/api/v1/persons", json={"first_name": "Ben", "last_name": "Zorn", "email": "b@x.de"})
    assert create_a.status_code == 201
    assert create_b.status_code == 201

    person_id = create_a.json()["data"]["person_id"]

    detail = client.get(f"/api/v1/persons/{person_id}")
    assert detail.status_code == 200
    assert detail.json()["data"]["person"]["email"] == "a@x.de"

    patched = client.patch(f"/api/v1/persons/{person_id}", json={"last_name": "Meier"})
    assert patched.status_code == 200
    assert patched.json()["data"]["last_name"] == "Meier"

    listed = client.get(
        "/api/v1/persons",
        params={"q": "ben", "sort_by": "first_name", "direction": "desc", "limit": 10, "offset": 0},
    )
    assert listed.status_code == 200
    assert listed.json()["data"]["pagination"]["total"] == 1
    assert listed.json()["data"]["items"][0]["first_name"] == "Ben"

    deleted = client.delete(f"/api/v1/persons/{person_id}")
    assert deleted.status_code == 204

    missing = client.get(f"/api/v1/persons/{person_id}")
    assert missing.status_code == 404


def test_person_validation_duplicate_not_allowed() -> None:
    client = create_test_client(app)

    payload = {"first_name": "Kira", "last_name": "Sommer", "email": "ks@example.com"}
    assert client.post("/api/v1/persons", json=payload).status_code == 201

    duplicate = client.post(
        "/api/v1/persons", json={"first_name": "kira", "last_name": "sommer", "email": "KS@example.com"}
    )
    assert duplicate.status_code == 409


def test_bank_assignment_and_allowances_flow() -> None:
    client = create_test_client(app)
    person = client.post("/api/v1/persons", json={"first_name": "Lena", "last_name": "Berg", "email": "l@example.com"})
    person_id = person.json()["data"]["person_id"]
    bank_id = str(uuid4())

    assignment = client.post(f"/api/v1/persons/{person_id}/banks/{bank_id}")
    assert assignment.status_code == 201

    duplicate_assignment = client.post(f"/api/v1/persons/{person_id}/banks/{bank_id}")
    assert duplicate_assignment.status_code == 409

    assignment_list = client.get(f"/api/v1/persons/{person_id}/banks")
    assert assignment_list.status_code == 200
    assert assignment_list.json()["data"]["total"] == 1

    allowance = client.put(f"/api/v1/persons/{person_id}/allowances/{bank_id}", params={"amount": "801.25"})
    assert allowance.status_code == 200
    assert allowance.json()["data"]["amount"] == "801.25"

    allowance_list = client.get(f"/api/v1/persons/{person_id}/allowances")
    assert allowance_list.status_code == 200
    assert allowance_list.json()["data"]["amount_total"] == "801.25"

    summary = client.get(f"/api/v1/persons/{person_id}/allowances/summary")
    assert summary.status_code == 200
    assert summary.json()["data"]["total_amount"] == "801.25"

    delete_assignment = client.delete(f"/api/v1/persons/{person_id}/banks/{bank_id}")
    assert delete_assignment.status_code == 204


def test_allowance_requires_assignment() -> None:
    client = create_test_client(app)
    person = client.post("/api/v1/persons", json={"first_name": "Noah", "last_name": "Krug", "email": "n@example.com"})
    person_id = person.json()["data"]["person_id"]
    bank_id = str(uuid4())

    response = client.put(f"/api/v1/persons/{person_id}/allowances/{bank_id}", params={"amount": "100.00"})
    assert response.status_code == 409


def test_mongo_persistence_inside_repository() -> None:
    client = create_test_client(app)

    created = client.post(
        "/api/v1/persons",
        json={"first_name": "Persist", "last_name": "Check", "email": "persist@example.com"},
    )
    assert created.status_code == 201
    person_id = created.json()["data"]["person_id"]

    repository = get_repository()
    person = repository.get_person(UUID(person_id))
    assert person is not None
    assert person.email == "persist@example.com"
