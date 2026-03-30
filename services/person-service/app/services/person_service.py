from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status

from app.models import (
    AllowanceListResponse,
    AllowanceSummaryBankItem,
    AllowanceSummaryResponse,
    AssignmentListResponse,
    PaginationMeta,
    Person,
    PersonBankAssignment,
    PersonCreate,
    PersonDetailResponse,
    PersonListItem,
    PersonListResponse,
    PersonSortField,
    PersonUpdate,
    SortDirection,
    TaxAllowance,
)
from app.repositories.person_repository import MongoPersonRepository, PersonRepository


class PersonService:
    def __init__(self, repository: PersonRepository) -> None:
        self.repository = repository

    def list_persons(
        self,
        *,
        q: str | None,
        sort_by: PersonSortField,
        direction: SortDirection,
        limit: int,
        offset: int,
    ) -> PersonListResponse:
        persons = self.repository.list_persons()

        if q:
            query = q.lower().strip()
            persons = [
                person
                for person in persons
                if query in person.first_name.lower()
                or query in person.last_name.lower()
                or (person.email and query in person.email)
            ]

        reverse = direction == SortDirection.DESC
        if sort_by == PersonSortField.CREATED_AT:
            persons = sorted(persons, key=lambda item: item.created_at, reverse=reverse)
        elif sort_by == PersonSortField.FIRST_NAME:
            persons = sorted(persons, key=lambda item: item.first_name.lower(), reverse=reverse)
        else:
            persons = sorted(persons, key=lambda item: item.last_name.lower(), reverse=reverse)

        total = len(persons)
        persons = persons[offset : offset + limit]

        items = [self._to_person_list_item(person) for person in persons]
        return PersonListResponse(
            items=items,
            pagination=PaginationMeta(limit=limit, offset=offset, returned=len(items), total=total),
        )

    def create_person(self, payload: PersonCreate) -> Person:
        self._assert_person_uniqueness(
            first_name=payload.first_name,
            last_name=payload.last_name,
            email=payload.email,
        )
        now = self._now()
        person = Person(**payload.model_dump(), created_at=now, updated_at=now)
        try:
            return self.repository.create_person(person)
        except Exception as exc:  # noqa: BLE001
            if MongoPersonRepository.is_duplicate_error(exc):
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Person bereits vorhanden") from exc
            raise

    def get_person(self, person_id: UUID) -> Person:
        person = self.repository.get_person(person_id)
        if person is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person nicht gefunden")
        return person

    def get_person_detail(self, person_id: UUID) -> PersonDetailResponse:
        person = self.get_person(person_id)
        return PersonDetailResponse(person=person, stats=self._to_person_list_item(person))

    def update_person(self, person_id: UUID, payload: PersonUpdate) -> Person:
        current = self.get_person(person_id)
        merged = current.model_copy(update=payload.model_dump(exclude_none=True))
        merged.updated_at = self._now()
        self._assert_person_uniqueness(
            first_name=merged.first_name,
            last_name=merged.last_name,
            email=merged.email,
            exclude_id=person_id,
        )
        try:
            return self.repository.update_person(merged)
        except Exception as exc:  # noqa: BLE001
            if MongoPersonRepository.is_duplicate_error(exc):
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Person bereits vorhanden") from exc
            raise

    def delete_person(self, person_id: UUID) -> None:
        deleted = self.repository.delete_person(person_id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person nicht gefunden")

    def list_assignments(self, person_id: UUID) -> AssignmentListResponse:
        self.get_person(person_id)
        items = sorted(self.repository.list_assignments(person_id), key=lambda item: item.assigned_at)
        return AssignmentListResponse(items=items, total=len(items))

    def create_assignment(self, person_id: UUID, bank_id: UUID) -> PersonBankAssignment:
        self.get_person(person_id)
        existing = self.repository.get_assignment(person_id, bank_id)
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Bankzuordnung bereits vorhanden")
        assignment = PersonBankAssignment(person_id=person_id, bank_id=bank_id, assigned_at=self._now())
        return self.repository.create_assignment(assignment)

    def delete_assignment(self, person_id: UUID, bank_id: UUID) -> None:
        self.get_person(person_id)
        deleted = self.repository.delete_assignment(person_id, bank_id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bankzuordnung nicht gefunden")

    def list_allowances(self, person_id: UUID) -> AllowanceListResponse:
        self.get_person(person_id)
        items = sorted(self.repository.list_allowances(person_id), key=lambda item: str(item.bank_id))
        amount_total = sum((item.amount for item in items), start=Decimal("0"))
        return AllowanceListResponse(items=items, total=len(items), amount_total=amount_total)

    def upsert_allowance(self, person_id: UUID, bank_id: UUID, amount: Decimal) -> TaxAllowance:
        self.get_person(person_id)
        assignment = self.repository.get_assignment(person_id, bank_id)
        if assignment is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Freibetrag nur für zugeordnete Banken zulässig",
            )

        allowance = TaxAllowance(
            person_id=person_id,
            bank_id=bank_id,
            amount=amount,
            updated_at=self._now(),
        )
        return self.repository.upsert_allowance(allowance)

    def allowance_summary(self, person_id: UUID) -> AllowanceSummaryResponse:
        self.get_person(person_id)
        items = sorted(self.repository.list_allowances(person_id), key=lambda item: str(item.bank_id))
        banks = [AllowanceSummaryBankItem(bank_id=item.bank_id, amount=item.amount) for item in items]
        total_amount = sum((item.amount for item in items), start=Decimal("0"))
        return AllowanceSummaryResponse(person_id=person_id, banks=banks, total_amount=total_amount, currency="EUR")

    def _to_person_list_item(self, person: Person) -> PersonListItem:
        assignments = self.repository.list_assignments(person.person_id)
        allowances = self.repository.list_allowances(person.person_id)
        allowance_total = sum((item.amount for item in allowances), start=Decimal("0"))
        return PersonListItem(
            person_id=person.person_id,
            first_name=person.first_name,
            last_name=person.last_name,
            email=person.email,
            bank_count=len(assignments),
            allowance_total=allowance_total,
        )

    def _assert_person_uniqueness(
        self,
        *,
        first_name: str,
        last_name: str,
        email: str | None,
        exclude_id: UUID | None = None,
    ) -> None:
        for existing in self.repository.list_persons():
            if exclude_id is not None and existing.person_id == exclude_id:
                continue
            if (
                existing.first_name.lower() == first_name.lower()
                and existing.last_name.lower() == last_name.lower()
                and (existing.email or "") == (email or "")
            ):
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Person bereits vorhanden")

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()
