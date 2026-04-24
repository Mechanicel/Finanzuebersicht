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
  portfolio_id?: string | null
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
  portfolio_id?: string | null
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
  portfolio_id?: string | null
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


export interface DepotHoldingWithSummary extends HoldingReadModel {
  portfolio_id: string
  portfolio_name: string
  marketdata?: DepotMarketdataHoldingSummaryItem | null
}

export interface DepotMarketdataHoldingSummaryItem {
  symbol: string
  name?: string | null
  company_name?: string | null
  sector?: string | null
  country?: string | null
  currency?: string | null
  current_price?: number | null
  last_price?: number | null
  market_cap?: number | null
  possibly_delisted?: boolean | null
  cache_status?: string | null
  as_of?: string | null
}

export interface DepotMarketdataHoldingsSummary {
  items: DepotMarketdataHoldingSummaryItem[]
  total: number
  source?: string | null
}

export interface DepotInstrumentTimeseriesPoint {
  date: string
  value: number
}

export interface DepotInstrumentTimeseries {
  symbol: string
  series: string
  benchmark_symbol: string
  instrument: { points: DepotInstrumentTimeseriesPoint[] }
  benchmark: { symbol: string; points: DepotInstrumentTimeseriesPoint[] }
  benchmark_data?: { available?: boolean }
  meta?: { warnings?: Array<{ code: string; message: string; symbol?: string }> }
}

export interface DepotInstrumentRisk {
  symbol: string
  benchmark: string
  aligned_points: number
  volatility_proxy?: number | null
  benchmark_volatility_proxy?: number | null
  meta?: { warnings?: Array<{ code: string; message: string; symbol?: string }> }
}

export interface DepotInstrumentBenchmarkSummary {
  symbol: string
  benchmark: string
  comparison?: DepotInstrumentTimeseries
}

export interface DepotBenchmarkCatalogItem {
  symbol: string
  name: string
}

export interface DepotInstrumentBenchmarkCatalog {
  items: DepotBenchmarkCatalogItem[]
  source?: string
}

export interface DepotInstrumentBenchmarkSearchResult {
  query: string
  items: DepotBenchmarkCatalogItem[]
  total: number
}

export type InstrumentType = 'EQUITY' | 'ETF' | 'MUTUALFUND' | 'INDEX' | 'UNKNOWN'

export interface DepotInstrumentFundamentals {
  symbol: string
  instrument_type?: InstrumentType | null
  company_name?: string | null
  sector?: string | null
  country?: string | null
  currency?: string | null
  exchange?: string | null
  website?: string | null
  description?: string | null
  // Market data from yfinance info
  market_cap?: number | null
  enterprise_value?: number | null
  trailing_pe?: number | null
  forward_pe?: number | null
  price_to_book?: number | null
  dividend_yield?: number | null
  beta?: number | null
  fifty_two_week_high?: number | null
  fifty_two_week_low?: number | null
  profit_margins?: number | null
  gross_margins?: number | null
  operating_margins?: number | null
  return_on_assets?: number | null
  return_on_equity?: number | null
  earnings_per_share?: number | null
  forward_eps?: number | null
  revenue_growth?: number | null
  debt_to_equity?: number | null
  current_ratio?: number | null
  ebitda?: number | null
  total_revenue?: number | null
  // ETF from info
  total_assets_aum?: number | null
  fund_family?: string | null
  fund_inception_date?: string | null
  fund_yield?: number | null
  ytd_return?: number | null
  [key: string]: unknown
}

export interface EtfHolding {
  symbol: string
  name?: string | null
  weight?: number | null
}

export interface EtfData {
  symbol: string
  instrument_type: InstrumentType
  funds_data_source?: string | null
  aum?: number | null
  fund_family?: string | null
  inception_date?: string | null
  legal_type?: string | null
  expense_ratio?: number | null
  fund_yield?: number | null
  ytd_return?: number | null
  three_year_return?: number | null
  five_year_return?: number | null
  top_holdings: EtfHolding[]
  sector_weights: Record<string, number>
  asset_classes: Record<string, number>
  equity_holdings: Record<string, number>
  fetched_at?: string | null
}

export interface DepotInstrumentFinancials {
  symbol: string
  period: 'annual' | 'quarterly'
  instrument_type?: InstrumentType | null
  currency?: string | null
  etf_data?: EtfData | null
  statements?: {
    income_statement?: DepotInstrumentIncomeStatementRow[]
    balance_sheet?: DepotInstrumentBalanceSheetStatementRow[]
    cash_flow?: DepotInstrumentCashFlowRow[]
  }
  derived?: DepotInstrumentFinancialDerivedFields
  meta?: DepotInstrumentFinancialMeta
}

export interface DepotInstrumentFinancialStatementRow {
  date?: string | null
  fiscalYear?: string | number | null
  period?: string | null
  reportedCurrency?: string | null
  [key: string]: unknown
}

export interface DepotInstrumentBalanceSheetStatementRow extends DepotInstrumentFinancialStatementRow {
  totalAssets?: number | null
  totalCurrentAssets?: number | null
  totalLiabilities?: number | null
  totalCurrentLiabilities?: number | null
  totalEquity?: number | null
  cashAndCashEquivalents?: number | null
  cashAndShortTermInvestments?: number | null
  totalDebt?: number | null
  netDebt?: number | null
  shortTermDebt?: number | null
  longTermDebt?: number | null
  accountsReceivable?: number | null
  inventory?: number | null
  accountsPayable?: number | null
  retainedEarnings?: number | null
  goodwillAndIntangibles?: number | null
  netPPE?: number | null
  workingCapital?: number | null
}

export interface DepotInstrumentIncomeStatementRow extends DepotInstrumentFinancialStatementRow {
  revenue?: number | null
  costOfRevenue?: number | null
  grossProfit?: number | null
  grossMargin?: number | null
  operatingIncome?: number | null
  operatingMargin?: number | null
  ebitda?: number | null
  ebit?: number | null
  netIncome?: number | null
  netMargin?: number | null
  interestExpense?: number | null
  taxProvision?: number | null
  pretaxIncome?: number | null
  epsDiluted?: number | null
  depreciationAmortization?: number | null
}

export interface DepotInstrumentCashFlowRow extends DepotInstrumentFinancialStatementRow {
  operatingCashFlow?: number | null
  capitalExpenditure?: number | null
  freeCashFlow?: number | null
  dividendsPaid?: number | null
  shareRepurchase?: number | null
  issuanceOfDebt?: number | null
  repaymentOfDebt?: number | null
  changeInWorkingCapital?: number | null
  investingCashFlow?: number | null
  financingCashFlow?: number | null
}

export interface DepotInstrumentFinancialDerivedFields {
  latest_period_date?: string | null
  total_debt?: number | null
  net_debt?: number | null
  free_cash_flow?: number | null
  roe?: number | null
  roa?: number | null
  debt_to_equity?: number | null
  current_ratio?: number | null
  gross_margin?: number | null
  operating_margin?: number | null
  net_margin?: number | null
  ebitda?: number | null
  ebitda_margin?: number | null
  market_cap?: number | null
  beta?: number | null
  [key: string]: unknown
}

export interface DepotInstrumentFinancialWarning {
  code: string
  message: string
  symbol?: string
}

export interface DepotInstrumentFinancialMeta {
  warnings?: DepotInstrumentFinancialWarning[]
  [key: string]: unknown
}


export interface DashboardReadModel {
  person_id: string
  overview: Record<string, unknown>
  allocation: { labels?: string[]; values?: number[] }
  metrics: Record<string, unknown>
  timeseries: { points?: { date: string; value: number }[] }
  kpis: Array<{ label: string; value: string | number }>
}

export type DashboardSectionState = 'ready' | 'stale' | 'pending' | 'error'

export interface DashboardSectionReadModel<TPayload> {
  person_id: string
  section: 'overview' | 'allocation' | 'timeseries' | 'metrics' | (string & {})
  state: DashboardSectionState
  generated_at: string | null
  stale_at: string | null
  refresh_in_progress: boolean
  warnings: string[]
  payload: TPayload
}

export interface DashboardOverviewPayload {
  kpis?: Array<{ label: string; value: string | number }>
  [key: string]: unknown
}

export interface DashboardAllocationPayload {
  labels?: string[]
  values?: number[]
  [key: string]: unknown
}

export interface DashboardTimeseriesPayload {
  points?: { date: string; value: number }[]
  [key: string]: unknown
}

export type DashboardMetricsPayload = Record<string, unknown>

export interface PortfolioSummaryReadModel {
  person_id: string
  as_of: string
  summary_kind?: 'snapshot'
  return_basis?: 'since_cost_basis'
  currency: string
  market_value: number
  invested_value: number
  unrealized_pnl: number
  unrealized_return_pct?: number | null
  portfolios_count: number
  holdings_count: number
  top_position_weight?: number | null
  top3_weight?: number | null
  warnings?: string[]
  meta: { loading?: boolean; error?: string | null; [key: string]: unknown }
}

export interface PortfolioPerformanceSummary {
  summary_kind?: 'range'
  return_basis?: 'range_start_value'
  start_value?: number | null
  end_value?: number | null
  absolute_change?: number | null
  return_pct?: number | null
}

export interface PortfolioPerformanceSeriesPoint {
  x: string
  y: number
}

export interface PortfolioPerformanceSeries {
  key: string
  label: string
  points: PortfolioPerformanceSeriesPoint[]
}

export interface PortfolioPerformanceReadModel {
  person_id: string
  range: string
  range_label?: string | null
  benchmark_symbol?: string | null
  series: PortfolioPerformanceSeries[]
  summary: PortfolioPerformanceSummary
  meta: { loading?: boolean; error?: string | null; [key: string]: unknown }
}

export type PortfolioDashboardRange = '1m' | '3m' | '6m' | 'ytd' | '1y' | 'max'

export interface PortfolioExposureSlice {
  label: string
  market_value: number
  weight: number
}

export interface PortfolioExposuresReadModel {
  person_id: string
  by_position: PortfolioExposureSlice[]
  by_sector: PortfolioExposureSlice[]
  by_country: PortfolioExposureSlice[]
  by_currency: PortfolioExposureSlice[]
  meta: { loading?: boolean; error?: string | null; [key: string]: unknown }
}

export interface PortfolioHoldingItem {
  portfolio_id: string
  portfolio_name?: string | null
  holding_id?: string | null
  symbol?: string | null
  display_name?: string | null
  quantity: number
  acquisition_price?: number | null
  current_price?: number | null
  invested_value: number
  market_value: number
  unrealized_pnl: number
  unrealized_return_pct?: number | null
  weight: number
  sector?: string | null
  country?: string | null
  currency?: string | null
  data_status: string
  warnings?: string[]
}

export interface PortfolioHoldingsReadModel {
  person_id: string
  as_of: string
  currency: string
  items: PortfolioHoldingItem[]
  summary: PortfolioSummaryReadModel
  meta: { loading?: boolean; error?: string | null; [key: string]: unknown }
}

export interface PortfolioRiskReadModel {
  person_id: string
  as_of: string
  range?: string
  range_label?: string | null
  methodology?: 'daily_returns_on_range' | (string & {})
  benchmark_relation?: 'relative_to_benchmark' | (string & {})
  benchmark_symbol?: string | null
  portfolio_volatility?: number | null
  max_drawdown?: number | null
  correlation?: number | null
  beta?: number | null
  tracking_error?: number | null
  annualized_volatility?: number | null
  annualized_tracking_error?: number | null
  sharpe_ratio?: number | null
  sortino_ratio?: number | null
  information_ratio?: number | null
  active_return?: number | null
  best_day_return?: number | null
  worst_day_return?: number | null
  aligned_points?: number | null
  top_position_weight?: number | null
  top3_weight?: number | null
  concentration_note?: string | null
  meta: { loading?: boolean; error?: string | null; [key: string]: unknown }
}

export interface PortfolioContributorItem {
  symbol?: string | null
  display_name?: string | null
  market_value: number
  weight: number
  unrealized_pnl: number
  contribution_weighted: number
  direction?: string | null
  contribution_return?: number | null
  contribution_pct_points?: number | null
  periods_used?: number
  history_available?: boolean
}

export interface PortfolioContributorsReadModel {
  person_id: string
  as_of?: string
  range?: string
  range_label?: string | null
  summary_kind?: 'range'
  return_basis?: 'range_contribution'
  methodology?: string
  total_contribution_return?: number | null
  total_contribution_pct_points?: number | null
  warnings?: string[]
  top_contributors: PortfolioContributorItem[]
  top_detractors: PortfolioContributorItem[]
  meta: { loading?: boolean; error?: string | null; [key: string]: unknown }
}

export interface PortfolioAttributionMethodology {
  key: string
  label: string
  description: string
  contribution_basis: string
  contribution_unit: 'percentage_points' | (string & {})
}

export interface PortfolioAttributionSummary {
  portfolio_return_pct?: number | null
  total_contribution_pct_points: number
  residual_pct_points?: number | null
  covered_positions: number
  total_positions: number
  unattributed_positions: number
}

export interface PortfolioAttributionItem {
  label: string
  contribution_pct_points: number
  return_pct?: number | null
  weight?: number | null
  market_value?: number | null
  direction?: 'positive' | 'negative' | 'neutral' | string | null
  symbol?: string | null
}

export type PortfolioAttributionBucketKey = 'position' | 'sector' | 'country' | 'currency'

export type PortfolioAttributionBucket =
  | PortfolioAttributionItem[]
  | {
      top_positive?: PortfolioAttributionItem[]
      top_negative?: PortfolioAttributionItem[]
      positive?: PortfolioAttributionItem[]
      negative?: PortfolioAttributionItem[]
      top_contributors?: PortfolioAttributionItem[]
      top_detractors?: PortfolioAttributionItem[]
      items?: PortfolioAttributionItem[]
      warnings?: string[]
      meta?: Record<string, unknown>
      [key: string]: unknown
    }

export interface PortfolioAttributionReadModel {
  person_id: string
  as_of: string
  range: string
  range_label?: string | null
  benchmark_symbol?: string | null
  methodology: PortfolioAttributionMethodology
  summary: PortfolioAttributionSummary
  by_position: PortfolioAttributionItem[]
  by_sector: PortfolioAttributionItem[]
  by_country: PortfolioAttributionItem[]
  by_currency: PortfolioAttributionItem[]
  warnings: string[]
  meta: { loading?: boolean; error?: string | null; [key: string]: unknown }
}

export interface PortfolioDataCoverageReadModel {
  person_id: string
  as_of: string
  total_holdings: number
  missing_prices: number
  missing_sectors: number
  missing_countries: number
  missing_currencies: number
  fallback_acquisition_prices?: number
  holdings_with_marketdata_warnings?: number
  warnings: string[]
  meta: { loading?: boolean; error?: string | null; [key: string]: unknown }
}

export interface PortfolioDashboardReadModel {
  person_id: string
  as_of: string
  range: string
  benchmark_symbol?: string | null
  summary: PortfolioSummaryReadModel
  performance: PortfolioPerformanceReadModel
  exposures: PortfolioExposuresReadModel
  holdings: PortfolioHoldingsReadModel
  risk: PortfolioRiskReadModel
  coverage: PortfolioDataCoverageReadModel
  contributors: PortfolioContributorsReadModel
  attribution?: PortfolioAttributionReadModel | null
  meta: { loading?: boolean; error?: string | null; warnings?: string[]; [key: string]: unknown }
}

export interface ApiEnvelope<T> { data: T }

// ---------------------------------------------------------------------------
// Smart Benchmark types
// ---------------------------------------------------------------------------

export interface BenchmarkComponent {
  ticker: string
  name?: string | null
  weight: number  // 0–100, must sum to 100
}

export interface BenchmarkConfig {
  components: BenchmarkComponent[]
}

export interface BenchmarkConfigReadModel {
  person_id: string
  components: BenchmarkComponent[]
  updated_at?: string | null
}

export interface BenchmarkSuggestionReadModel {
  person_id: string
  components: BenchmarkComponent[]
  reasoning: string
}
