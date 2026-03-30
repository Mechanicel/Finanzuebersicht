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
