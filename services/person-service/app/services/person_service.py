from __future__ import annotations

from datetime import UTC, datetime
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status

from app.models import (
    AllowanceListResponse,
    AllowanceUpsertRequest,
    AllowanceSummaryBankItem,
    AllowanceSummaryResponse,
    AssignmentListResponse,
    FilingStatus,
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
    TaxCountry,
    TaxProfile,
)
from app.repositories.person_repository import MongoPersonRepository, PersonRepository


@dataclass(frozen=True)
class AllowancePolicy:
    annual_limit: Decimal
    currency: str
    rule_name: str


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
            persons = [person for person in persons if self._matches_person_query(person, q)]

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
        update_values = payload.model_dump(exclude_none=True)
        tax_profile_patch = update_values.pop("tax_profile", None)
        merged = current.model_copy(update=update_values)
        if tax_profile_patch is not None:
            merged.tax_profile = current.tax_profile.model_copy(update=tax_profile_patch)
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

    def list_allowances(self, person_id: UUID, tax_year: int | None = None) -> AllowanceListResponse:
        self.get_person(person_id)
        items = sorted(
            self.repository.list_allowances(person_id, tax_year=tax_year),
            key=lambda item: (item.tax_year, str(item.bank_id)),
        )
        amount_total = sum((item.amount for item in items), start=Decimal("0"))
        return AllowanceListResponse(items=items, total=len(items), amount_total=amount_total)

    def upsert_allowance(self, person_id: UUID, bank_id: UUID, payload: AllowanceUpsertRequest) -> TaxAllowance:
        person = self.get_person(person_id)
        assignment = self.repository.get_assignment(person_id, bank_id)
        if assignment is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Freibetrag nur für zugeordnete Banken zulässig",
            )
        policy = self._resolve_allowance_policy(person.tax_profile)
        if payload.currency != policy.currency:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Für {policy.rule_name} ist aktuell nur {policy.currency} zulässig",
            )

        current_year_allowances = self.repository.list_allowances(person_id, tax_year=payload.tax_year)
        total_other_banks = sum(
            (item.amount for item in current_year_allowances if item.bank_id != bank_id),
            start=Decimal("0"),
        )
        requested_total = total_other_banks + payload.amount
        if requested_total > policy.annual_limit:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Sparer-Pauschbetrag überschritten: {requested_total} {policy.currency} > "
                    f"{policy.annual_limit} {policy.currency} für Steuerjahr {payload.tax_year}"
                ),
            )

        allowance = TaxAllowance(
            person_id=person_id,
            bank_id=bank_id,
            tax_year=payload.tax_year,
            amount=payload.amount,
            currency=payload.currency,
            updated_at=self._now(),
        )
        return self.repository.upsert_allowance(allowance)

    def allowance_summary(self, person_id: UUID, tax_year: int) -> AllowanceSummaryResponse:
        person = self.get_person(person_id)
        policy = self._resolve_allowance_policy(person.tax_profile)
        items = sorted(self.repository.list_allowances(person_id, tax_year=tax_year), key=lambda item: str(item.bank_id))
        banks = [AllowanceSummaryBankItem(bank_id=item.bank_id, tax_year=item.tax_year, amount=item.amount) for item in items]
        total_amount = sum((item.amount for item in items), start=Decimal("0"))
        remaining_amount = max(Decimal("0"), policy.annual_limit - total_amount)
        return AllowanceSummaryResponse(
            person_id=person_id,
            tax_year=tax_year,
            banks=banks,
            total_amount=total_amount,
            annual_limit=policy.annual_limit,
            remaining_amount=remaining_amount,
            currency=policy.currency,
            applied_rule=policy.rule_name,
        )

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

    @staticmethod
    def _matches_person_query(person: Person, q: str) -> bool:
        query = q.strip().lower()
        if not query:
            return True

        tokens = [token for token in query.split() if token]
        first_name = person.first_name.lower()
        last_name = person.last_name.lower()
        full_name = f"{first_name} {last_name}"
        email = (person.email or "").lower()

        if query in first_name or query in last_name or (email and query in email) or query in full_name:
            return True

        if not tokens:
            return False

        searchable_parts = [first_name, last_name, full_name]
        if email:
            searchable_parts.append(email)
        return all(any(token in part for part in searchable_parts) for token in tokens)

    @staticmethod
    def _resolve_allowance_policy(tax_profile: TaxProfile) -> AllowancePolicy:
        if tax_profile.tax_country == TaxCountry.DE and tax_profile.filing_status == FilingStatus.JOINT:
            return AllowancePolicy(annual_limit=Decimal("2000"), currency="EUR", rule_name="DE/joint")
        if tax_profile.tax_country == TaxCountry.DE and tax_profile.filing_status == FilingStatus.SINGLE:
            return AllowancePolicy(annual_limit=Decimal("1000"), currency="EUR", rule_name="DE/single")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Steuerprofil wird für Freibeträge noch nicht unterstützt",
        )
