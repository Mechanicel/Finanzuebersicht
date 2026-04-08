export interface PersonReadModel {
  person_id: string
  first_name: string
  last_name: string
  email: string | null
  tax_profile: TaxProfileModel
  created_at: string
  updated_at: string
}

export type TaxCountryCode = 'DE' | (string & {})
export type FilingStatus = 'single' | 'joint'

export interface TaxProfileModel {
  tax_country: TaxCountryCode
  filing_status: FilingStatus
}

export interface PersonListItem {
  person_id: string
  first_name: string
  last_name: string
  email: string | null
  bank_count: number
  allowance_total: string
}

export interface PersonListReadModel {
  items: PersonListItem[]
  pagination: { limit: number; offset: number; returned: number; total: number }
}

export interface PersonDetailReadModel {
  person: PersonReadModel
  stats: PersonListItem
}


export interface PersonQueryParams {
  q?: string
  sort_by?: string
  direction?: 'asc' | 'desc'
  limit?: number
  offset?: number
}

export interface PersonCreatePayload {
  first_name: string
  last_name: string
  email?: string
}

export interface PersonUpdatePayload {
  first_name?: string
  last_name?: string
  email?: string
  tax_profile?: {
    tax_country?: string
    filing_status?: FilingStatus
  }
}


export interface BankReadModel {
  bank_id: string
  name: string
  bic: string
  blz: string
  country_code: string
}

export interface BankListReadModel {
  items: BankReadModel[]
  total: number
}

export interface BankCreatePayload {
  name: string
  bic: string
  blz: string
  country_code: string
}

export interface PersonBankAssignmentReadModel {
  person_id: string
  bank_id: string
  assigned_at: string
}

export interface AssignmentListReadModel {
  items: PersonBankAssignmentReadModel[]
  total: number
}

export interface TaxAllowanceReadModel {
  person_id: string
  bank_id: string
  tax_year: number
  amount: string
  currency: string
  updated_at: string
}

export interface AllowanceListReadModel {
  items: TaxAllowanceReadModel[]
  total: number
  amount_total: string
}

export interface AllowanceSummaryBankItemReadModel {
  bank_id: string
  tax_year: number
  amount: string
}

export interface AllowanceSummaryReadModel {
  person_id: string
  tax_year: number
  banks: AllowanceSummaryBankItemReadModel[]
  total_amount: string
  annual_limit: string
  remaining_amount: string
  currency: string
  tax_profile?: TaxProfileModel | null
}

export interface AllowanceUpsertPayload {
  tax_year: number
  amount: string
  currency?: string
}

export type AccountType = 'girokonto' | 'tagesgeldkonto' | 'festgeldkonto' | 'depot'

export interface AccountReadModel {
  account_id: string
  person_id: string
  bank_id: string
  account_type: AccountType
  label: string
  balance: string
  currency: string
  created_at: string
  updated_at: string
  account_number?: string | null
  depot_number?: string | null
  iban?: string | null
  opening_date?: string | null
  interest_rate?: string | null
  payout_account_iban?: string | null
  settlement_account_iban?: string | null
}


export interface AccountCreatePayload {
  bank_id: string
  account_type: AccountType
  label: string
  balance: string
  currency?: string
  account_number?: string | null
  depot_number?: string | null
  iban?: string | null
  opening_date?: string | null
  interest_rate?: string | null
  payout_account_iban?: string | null
  settlement_account_iban?: string | null
}

export interface AccountUpdatePayload {
  bank_id?: string
  account_type?: AccountType
  label?: string
  balance?: string
  currency?: string
  account_number?: string | null
  depot_number?: string | null
  iban?: string | null
  opening_date?: string | null
  interest_rate?: string | null
  payout_account_iban?: string | null
  settlement_account_iban?: string | null
}

export interface PortfolioReadModel {
  portfolio_id: string
  person_id: string
  display_name: string
  created_at: string
  updated_at: string
}

export interface PortfolioListReadModel {
  items: PortfolioReadModel[]
  total: number
}

export interface HoldingReadModel {
  holding_id: string
  portfolio_id: string
  symbol: string
  isin?: string | null
  wkn?: string | null
  company_name?: string | null
  display_name?: string | null
  quantity: number
  acquisition_price: number
  current_price?: number | null
  current_price_updated_at?: string | null
  currency: string
  buy_date: string
  notes?: string | null
  created_at: string
  updated_at: string
}

export interface PortfolioDetailReadModel extends PortfolioReadModel {
  holdings: HoldingReadModel[]
}

export interface PortfolioCreatePayload {
  display_name: string
}

export interface HoldingCreatePayload {
  symbol: string
  isin?: string | null
  wkn?: string | null
  company_name?: string | null
  display_name?: string | null
  quantity: number
  acquisition_price: number
  currency: string
  buy_date: string
  notes?: string | null
}

export interface HoldingUpdatePayload {
  quantity?: number
  acquisition_price?: number
  currency?: string
  buy_date?: string
  notes?: string | null
}

export interface HoldingsRefreshStubResponse {
  portfolio_id: string
  status: string
  accepted: boolean
  detail: string
}

export interface InstrumentPriceRefreshResponse {
  symbol: string
  trade_date: string
  current_price: number
  price_source: 'cache_today' | 'yfinance_1d_1m'
  price_cache_hit: boolean
  history_cache_present: boolean
  history_action: 'seed_max_in_background' | 'enrich_in_background'
  fetched_at: string
}


export type InstrumentHistoryRange = '1m' | '3m' | '6m' | 'ytd' | '1y' | 'max'

export interface InstrumentHistoryPoint {
  date: string
  close: number
}

export interface InstrumentHistoryResponse {
  symbol: string
  range: InstrumentHistoryRange
  points: InstrumentHistoryPoint[]
  cache_present: boolean
  updated_at: string
}

export interface InstrumentSearchItem {
  symbol: string
  company_name: string
  display_name?: string | null
  currency?: string | null
  exchange?: string | null
  exchange_full_name?: string | null
}

export interface InstrumentSearchResult {
  query: string
  items: InstrumentSearchItem[]
  total: number
}

export interface MarketdataProfile {
  symbol: string
  company_name: string
  price?: number | null
  last_price?: number | null
  currency?: string | null
  isin?: string | null
  wkn?: string | null
  exchange?: string | null
  exchange_full_name?: string | null
  quote_type?: string | null
  asset_type?: string | null
  industry?: string | null
  website?: string | null
  description?: string | null
  ceo?: string | null
  sector?: string | null
  country?: string | null
  phone?: string | null
  image?: string | null
  address?: string | null
  city?: string | null
  zip?: string | null
  address_line?: string | null
}

export interface DashboardReadModel {
  person_id: string
  overview: Record<string, unknown>
  allocation: { labels?: string[]; values?: number[] }
  metrics: Record<string, unknown>
  timeseries: { points?: { date: string; value: number }[] }
  kpis: Array<{ label: string; value: string | number }>
}
export interface ApiEnvelope<T> { data: T }
