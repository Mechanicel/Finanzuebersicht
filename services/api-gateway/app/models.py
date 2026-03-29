from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class PersonListItem(BaseModel):
    person_id: UUID
    display_name: str


class PersonListReadModel(BaseModel):
    items: list[PersonListItem]
    total: int


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
