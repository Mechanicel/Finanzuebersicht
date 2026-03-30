from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal
from uuid import UUID

from pymongo import ASCENDING
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

from app.models import Person, PersonBankAssignment, TaxAllowance


class PersonRepository(ABC):
    @abstractmethod
    def list_persons(self) -> list[Person]: ...

    @abstractmethod
    def create_person(self, person: Person) -> Person: ...

    @abstractmethod
    def get_person(self, person_id: UUID) -> Person | None: ...

    @abstractmethod
    def update_person(self, person: Person) -> Person: ...

    @abstractmethod
    def delete_person(self, person_id: UUID) -> bool: ...

    @abstractmethod
    def list_assignments(self, person_id: UUID) -> list[PersonBankAssignment]: ...

    @abstractmethod
    def get_assignment(self, person_id: UUID, bank_id: UUID) -> PersonBankAssignment | None: ...

    @abstractmethod
    def create_assignment(self, assignment: PersonBankAssignment) -> PersonBankAssignment: ...

    @abstractmethod
    def delete_assignment(self, person_id: UUID, bank_id: UUID) -> bool: ...

    @abstractmethod
    def list_allowances(self, person_id: UUID) -> list[TaxAllowance]: ...

    @abstractmethod
    def get_allowance(self, person_id: UUID, bank_id: UUID) -> TaxAllowance | None: ...

    @abstractmethod
    def upsert_allowance(self, allowance: TaxAllowance) -> TaxAllowance: ...


class MongoPersonRepository(PersonRepository):
    def __init__(
        self,
        database: Database,
        *,
        person_collection: str,
        assignment_collection: str,
        allowance_collection: str,
    ) -> None:
        self._persons: Collection = database[person_collection]
        self._assignments: Collection = database[assignment_collection]
        self._allowances: Collection = database[allowance_collection]
        self._ensure_indexes()

    def _ensure_indexes(self) -> None:
        self._persons.create_index([("person_id", ASCENDING)], unique=True)
        self._persons.create_index([("dedupe_key", ASCENDING)], unique=True)
        self._assignments.create_index([("person_id", ASCENDING), ("bank_id", ASCENDING)], unique=True)
        self._allowances.create_index([("person_id", ASCENDING), ("bank_id", ASCENDING)], unique=True)

    def list_persons(self) -> list[Person]:
        return [self._person_from_doc(doc) for doc in self._persons.find({}, {"_id": 0})]

    def create_person(self, person: Person) -> Person:
        self._persons.insert_one(self._person_to_doc(person))
        return person

    def get_person(self, person_id: UUID) -> Person | None:
        doc = self._persons.find_one({"person_id": str(person_id)}, {"_id": 0})
        if doc is None:
            return None
        return self._person_from_doc(doc)

    def update_person(self, person: Person) -> Person:
        self._persons.replace_one({"person_id": str(person.person_id)}, self._person_to_doc(person), upsert=False)
        return person

    def delete_person(self, person_id: UUID) -> bool:
        person_id_str = str(person_id)
        deleted = self._persons.delete_one({"person_id": person_id_str}).deleted_count > 0
        if deleted:
            self._assignments.delete_many({"person_id": person_id_str})
            self._allowances.delete_many({"person_id": person_id_str})
        return deleted

    def list_assignments(self, person_id: UUID) -> list[PersonBankAssignment]:
        docs = self._assignments.find({"person_id": str(person_id)}, {"_id": 0})
        return [self._assignment_from_doc(doc) for doc in docs]

    def get_assignment(self, person_id: UUID, bank_id: UUID) -> PersonBankAssignment | None:
        doc = self._assignments.find_one({"person_id": str(person_id), "bank_id": str(bank_id)}, {"_id": 0})
        if doc is None:
            return None
        return self._assignment_from_doc(doc)

    def create_assignment(self, assignment: PersonBankAssignment) -> PersonBankAssignment:
        self._assignments.insert_one(self._assignment_to_doc(assignment))
        return assignment

    def delete_assignment(self, person_id: UUID, bank_id: UUID) -> bool:
        deleted = (
            self._assignments.delete_one({"person_id": str(person_id), "bank_id": str(bank_id)}).deleted_count > 0
        )
        if deleted:
            self._allowances.delete_one({"person_id": str(person_id), "bank_id": str(bank_id)})
        return deleted

    def list_allowances(self, person_id: UUID) -> list[TaxAllowance]:
        docs = self._allowances.find({"person_id": str(person_id)}, {"_id": 0})
        return [self._allowance_from_doc(doc) for doc in docs]

    def get_allowance(self, person_id: UUID, bank_id: UUID) -> TaxAllowance | None:
        doc = self._allowances.find_one({"person_id": str(person_id), "bank_id": str(bank_id)}, {"_id": 0})
        if doc is None:
            return None
        return self._allowance_from_doc(doc)

    def upsert_allowance(self, allowance: TaxAllowance) -> TaxAllowance:
        self._allowances.replace_one(
            {"person_id": str(allowance.person_id), "bank_id": str(allowance.bank_id)},
            self._allowance_to_doc(allowance),
            upsert=True,
        )
        return allowance

    @staticmethod
    def is_duplicate_error(exc: Exception) -> bool:
        return isinstance(exc, DuplicateKeyError)

    @staticmethod
    def _person_to_doc(person: Person) -> dict[str, str | None]:
        return {
            "person_id": str(person.person_id),
            "first_name": person.first_name,
            "last_name": person.last_name,
            "email": person.email,
            "dedupe_key": MongoPersonRepository._dedupe_key(person.first_name, person.last_name, person.email),
            "created_at": person.created_at,
            "updated_at": person.updated_at,
        }

    @staticmethod
    def _person_from_doc(doc: dict) -> Person:
        return Person.model_validate(doc)

    @staticmethod
    def _dedupe_key(first_name: str, last_name: str, email: str | None) -> str:
        return f"{first_name.strip().lower()}|{last_name.strip().lower()}|{(email or '').strip().lower()}"

    @staticmethod
    def _assignment_to_doc(assignment: PersonBankAssignment) -> dict[str, str]:
        return {
            "person_id": str(assignment.person_id),
            "bank_id": str(assignment.bank_id),
            "assigned_at": assignment.assigned_at,
        }

    @staticmethod
    def _assignment_from_doc(doc: dict) -> PersonBankAssignment:
        return PersonBankAssignment.model_validate(doc)

    @staticmethod
    def _allowance_to_doc(allowance: TaxAllowance) -> dict[str, str]:
        return {
            "person_id": str(allowance.person_id),
            "bank_id": str(allowance.bank_id),
            "amount": str(allowance.amount),
            "currency": allowance.currency,
            "updated_at": allowance.updated_at,
        }

    @staticmethod
    def _allowance_from_doc(doc: dict) -> TaxAllowance:
        allowance_doc = dict(doc)
        allowance_doc["amount"] = Decimal(allowance_doc["amount"])
        return TaxAllowance.model_validate(allowance_doc)
