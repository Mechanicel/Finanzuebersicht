from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class PersonReadModel(BaseModel):
    person_id: UUID
    first_name: str
    last_name: str
    email: str | None
    created_at: str
    updated_at: str


class PersonCreatePayload(BaseModel):
    first_name: str
    last_name: str
    email: str | None = None


class PersonUpdatePayload(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None


class PersonListItem(BaseModel):
    person_id: UUID
    first_name: str
    last_name: str
    email: str | None
    bank_count: int
    allowance_total: str


class PersonListPagination(BaseModel):
    limit: int
    offset: int
    returned: int
    total: int


class PersonListReadModel(BaseModel):
    items: list[PersonListItem]
    pagination: PersonListPagination


class PersonDetailReadModel(BaseModel):
    person: PersonReadModel
    stats: PersonListItem


class BankReadModel(BaseModel):
    bank_id: UUID
    name: str
    bic: str
    blz: str
    country_code: str


class BankCreatePayload(BaseModel):
    name: str
    bic: str
    blz: str
    country_code: str = Field(default="DE", min_length=2, max_length=2)


class BankListReadModel(BaseModel):
    items: list[BankReadModel]
    total: int


class PersonBankAssignmentReadModel(BaseModel):
    person_id: UUID
    bank_id: UUID
    assigned_at: str


class AssignmentListReadModel(BaseModel):
    items: list[PersonBankAssignmentReadModel]
    total: int


class TaxAllowanceReadModel(BaseModel):
    person_id: UUID
    bank_id: UUID
    amount: str
    currency: str
    updated_at: str


class AllowanceListReadModel(BaseModel):
    items: list[TaxAllowanceReadModel]
    total: int
    amount_total: str


class AllowanceSummaryBankItemReadModel(BaseModel):
    bank_id: UUID
    amount: str


class AllowanceSummaryReadModel(BaseModel):
    person_id: UUID
    banks: list[AllowanceSummaryBankItemReadModel]
    total_amount: str
    currency: str


class AccountReadModel(BaseModel):
    account_id: UUID
    name: str
    type: str
    balance: float


class PortfolioReadModel(BaseModel):
    portfolio_id: UUID
    label: str
    total_value: float


class DashboardReadModel(BaseModel):
    person_id: UUID
    overview: dict
    allocation: dict
    metrics: dict
    timeseries: dict
    kpis: list[dict] = Field(default_factory=list)


class HealthDependency(BaseModel):
    service: str
    status: str
    detail: str | None = None


class GatewayHealthReadModel(BaseModel):
    status: str
    dependencies: list[HealthDependency]
