from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

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


class InMemoryPersonRepository(PersonRepository):
    def __init__(self) -> None:
        self._persons: dict[UUID, Person] = {}
        self._assignments: dict[tuple[UUID, UUID], PersonBankAssignment] = {}
        self._allowances: dict[tuple[UUID, UUID], TaxAllowance] = {}

    def list_persons(self) -> list[Person]:
        return list(self._persons.values())

    def create_person(self, person: Person) -> Person:
        self._persons[person.person_id] = person
        return person

    def get_person(self, person_id: UUID) -> Person | None:
        return self._persons.get(person_id)

    def update_person(self, person: Person) -> Person:
        self._persons[person.person_id] = person
        return person

    def delete_person(self, person_id: UUID) -> bool:
        deleted = self._persons.pop(person_id, None) is not None
        if deleted:
            assignment_keys = [key for key in self._assignments if key[0] == person_id]
            for key in assignment_keys:
                self._assignments.pop(key, None)
                self._allowances.pop(key, None)
            allowance_keys = [key for key in self._allowances if key[0] == person_id]
            for key in allowance_keys:
                self._allowances.pop(key, None)
        return deleted

    def list_assignments(self, person_id: UUID) -> list[PersonBankAssignment]:
        return [assignment for assignment in self._assignments.values() if assignment.person_id == person_id]

    def get_assignment(self, person_id: UUID, bank_id: UUID) -> PersonBankAssignment | None:
        return self._assignments.get((person_id, bank_id))

    def create_assignment(self, assignment: PersonBankAssignment) -> PersonBankAssignment:
        self._assignments[(assignment.person_id, assignment.bank_id)] = assignment
        return assignment

    def delete_assignment(self, person_id: UUID, bank_id: UUID) -> bool:
        deleted = self._assignments.pop((person_id, bank_id), None) is not None
        if deleted:
            self._allowances.pop((person_id, bank_id), None)
        return deleted

    def list_allowances(self, person_id: UUID) -> list[TaxAllowance]:
        return [allowance for allowance in self._allowances.values() if allowance.person_id == person_id]

    def get_allowance(self, person_id: UUID, bank_id: UUID) -> TaxAllowance | None:
        return self._allowances.get((person_id, bank_id))

    def upsert_allowance(self, allowance: TaxAllowance) -> TaxAllowance:
        self._allowances[(allowance.person_id, allowance.bank_id)] = allowance
        return allowance
