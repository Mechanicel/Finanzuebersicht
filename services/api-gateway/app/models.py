from __future__ import annotations

from datetime import date
from uuid import UUID

from typing import Literal

from pydantic import BaseModel, Field


class TaxProfileModel(BaseModel):
    tax_country: Literal["DE"] = "DE"
    filing_status: Literal["single", "joint"] = "single"


class TaxProfileUpdateModel(BaseModel):
    tax_country: Literal["DE"] | None = None
    filing_status: Literal["single", "joint"] | None = None


class PersonReadModel(BaseModel):
    person_id: UUID
    first_name: str
    last_name: str
    email: str | None
    tax_profile: TaxProfileModel
    created_at: str
    updated_at: str


class PersonCreatePayload(BaseModel):
    first_name: str
    last_name: str
    email: str | None = None
    tax_profile: TaxProfileModel = Field(default_factory=TaxProfileModel)


class PersonUpdatePayload(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    tax_profile: TaxProfileUpdateModel | None = None


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
    tax_year: int
    amount: str
    currency: str
    updated_at: str


class AllowanceUpsertPayload(BaseModel):
    tax_year: int
    amount: str
    currency: str = "EUR"


class AllowanceListReadModel(BaseModel):
    items: list[TaxAllowanceReadModel]
    total: int
    amount_total: str


class AllowanceSummaryBankItemReadModel(BaseModel):
    bank_id: UUID
    tax_year: int
    amount: str


class AllowanceSummaryReadModel(BaseModel):
    person_id: UUID
    tax_year: int
    banks: list[AllowanceSummaryBankItemReadModel]
    total_amount: str
    annual_limit: str
    remaining_amount: str
    currency: str
    applied_rule: str | None = None
    tax_profile: TaxProfileModel | None = None


class AccountReadModel(BaseModel):
    account_id: UUID
    person_id: UUID
    bank_id: UUID
    account_type: Literal["girokonto", "tagesgeldkonto", "festgeldkonto", "depot"]
    label: str
    balance: str
    currency: str
    created_at: str
    updated_at: str
    account_number: str | None = None
    depot_number: str | None = None
    iban: str | None = None
    opening_date: str | None = None
    interest_rate: str | None = None
    payout_account_iban: str | None = None
    settlement_account_iban: str | None = None


class AccountCreatePayload(BaseModel):
    bank_id: UUID
    account_type: Literal["girokonto", "tagesgeldkonto", "festgeldkonto", "depot"]
    label: str
    balance: str
    currency: str = "EUR"
    account_number: str | None = None
    depot_number: str | None = None
    iban: str | None = None
    opening_date: str | None = None
    interest_rate: str | None = None
    payout_account_iban: str | None = None
    settlement_account_iban: str | None = None


class AccountUpdatePayload(BaseModel):
    bank_id: UUID | None = None
    account_type: Literal["girokonto", "tagesgeldkonto", "festgeldkonto", "depot"] | None = None
    label: str | None = None
    balance: str | None = None
    currency: str | None = None
    account_number: str | None = None
    depot_number: str | None = None
    iban: str | None = None
    opening_date: str | None = None
    interest_rate: str | None = None
    payout_account_iban: str | None = None
    settlement_account_iban: str | None = None




class PortfolioCreatePayload(BaseModel):
    display_name: str


class HoldingCreatePayload(BaseModel):
    symbol: str
    isin: str | None = None
    wkn: str | None = None
    company_name: str | None = None
    display_name: str | None = None
    quantity: float
    acquisition_price: float
    currency: str = "EUR"
    buy_date: str
    notes: str | None = None


class HoldingUpdatePayload(BaseModel):
    quantity: float | None = None
    acquisition_price: float | None = None
    currency: str | None = None
    buy_date: str | None = None
    notes: str | None = None


class HoldingReadModel(HoldingCreatePayload):
    holding_id: UUID
    portfolio_id: UUID
    created_at: str
    updated_at: str


class PortfolioReadModel(BaseModel):
    portfolio_id: UUID
    person_id: UUID
    display_name: str
    created_at: str
    updated_at: str


class PortfolioListReadModel(BaseModel):
    items: list[PortfolioReadModel]
    total: int


class PortfolioDetailReadModel(PortfolioReadModel):
    holdings: list[HoldingReadModel]


class HoldingsRefreshStubReadModel(BaseModel):
    portfolio_id: UUID
    status: str
    accepted: bool
    detail: str




class MarketdataProfileReadModel(BaseModel):
    symbol: str
    company_name: str
    price: float | None = None
    currency: str | None = None
    isin: str | None = None
    exchange: str | None = None
    exchange_full_name: str | None = None
    industry: str | None = None
    website: str | None = None
    description: str | None = None
    ceo: str | None = None
    sector: str | None = None
    country: str | None = None
    phone: str | None = None
    image: str | None = None
    address: str | None = None
    city: str | None = None
    zip: str | None = None
    address_line: str | None = None

class DashboardReadModel(BaseModel):
    person_id: UUID
    overview: dict
    allocation: dict
    metrics: dict
    timeseries: dict
    kpis: list[dict] = Field(default_factory=list)


class PortfolioSummaryReadModel(BaseModel):
    person_id: UUID
    as_of: date
    currency: str = "EUR"
    market_value: float
    invested_value: float
    unrealized_pnl: float
    unrealized_return_pct: float | None = None
    portfolios_count: int
    holdings_count: int
    top_position_weight: float | None = None
    top3_weight: float | None = None
    meta: dict = Field(default_factory=dict)


class PortfolioPerformanceSummary(BaseModel):
    start_value: float | None = None
    end_value: float | None = None
    absolute_change: float | None = None
    return_pct: float | None = None


class PortfolioPerformanceReadModel(BaseModel):
    person_id: UUID
    range: str
    benchmark_symbol: str | None = None
    series: list[dict] = Field(default_factory=list)
    summary: PortfolioPerformanceSummary
    meta: dict = Field(default_factory=dict)


class PortfolioExposureSliceReadModel(BaseModel):
    label: str
    market_value: float
    weight: float


class PortfolioExposuresReadModel(BaseModel):
    person_id: UUID
    by_position: list[PortfolioExposureSliceReadModel] = Field(default_factory=list)
    by_sector: list[PortfolioExposureSliceReadModel] = Field(default_factory=list)
    by_country: list[PortfolioExposureSliceReadModel] = Field(default_factory=list)
    by_currency: list[PortfolioExposureSliceReadModel] = Field(default_factory=list)
    meta: dict = Field(default_factory=dict)


class PortfolioHoldingItemReadModel(BaseModel):
    portfolio_id: str
    portfolio_name: str | None = None
    holding_id: str | None = None
    symbol: str | None = None
    display_name: str | None = None
    quantity: float
    acquisition_price: float | None = None
    current_price: float | None = None
    invested_value: float
    market_value: float
    unrealized_pnl: float
    unrealized_return_pct: float | None = None
    weight: float
    sector: str | None = None
    country: str | None = None
    currency: str | None = None
    data_status: str
    warnings: list[str] = Field(default_factory=list)


class PortfolioHoldingsReadModel(BaseModel):
    person_id: UUID
    as_of: date
    currency: str = "EUR"
    items: list[PortfolioHoldingItemReadModel] = Field(default_factory=list)
    summary: PortfolioSummaryReadModel
    meta: dict = Field(default_factory=dict)


class PortfolioRiskReadModel(BaseModel):
    person_id: UUID
    as_of: date
    benchmark_symbol: str | None = None
    portfolio_volatility: float | None = None
    max_drawdown: float | None = None
    top_position_weight: float | None = None
    top3_weight: float | None = None
    concentration_note: str | None = None
    meta: dict = Field(default_factory=dict)


class PortfolioContributorReadModel(BaseModel):
    symbol: str | None = None
    display_name: str | None = None
    market_value: float
    weight: float
    unrealized_pnl: float
    contribution_weighted: float
    direction: str | None = None


class PortfolioContributorsReadModel(BaseModel):
    person_id: UUID
    top_contributors: list[PortfolioContributorReadModel] = Field(default_factory=list)
    top_detractors: list[PortfolioContributorReadModel] = Field(default_factory=list)
    meta: dict = Field(default_factory=dict)


class PortfolioDataCoverageReadModel(BaseModel):
    person_id: UUID
    as_of: date
    total_holdings: int
    missing_prices: int
    missing_sectors: int
    missing_countries: int
    missing_currencies: int
    warnings: list[str] = Field(default_factory=list)
    meta: dict = Field(default_factory=dict)


class HealthDependency(BaseModel):
    service: str
    status: str
    detail: str | None = None


class GatewayHealthReadModel(BaseModel):
    status: str
    dependencies: list[HealthDependency]
