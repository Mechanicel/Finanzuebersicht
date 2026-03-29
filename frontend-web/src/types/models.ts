export interface PersonListItem { person_id: string; display_name: string }
export interface PersonListReadModel { items: PersonListItem[]; total: number }
export interface AccountReadModel { account_id: string; name: string; type: string; balance: number }
export interface PortfolioReadModel { portfolio_id: string; label: string; total_value: number }
export interface DashboardReadModel {
  person_id: string
  overview: Record<string, unknown>
  allocation: { labels?: string[]; values?: number[] }
  metrics: Record<string, unknown>
  timeseries: { points?: { date: string; value: number }[] }
  kpis: Array<{ label: string; value: string | number }>
}
export interface ApiEnvelope<T> { data: T }
