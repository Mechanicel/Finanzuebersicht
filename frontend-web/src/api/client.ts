import { http } from './http'
import type {
  AccountCreatePayload,
  AccountReadModel,
  AccountUpdatePayload,
  AllowanceListReadModel,
  AllowanceSummaryReadModel,
  AllowanceUpsertPayload,
  AssignmentListReadModel,
  ApiEnvelope,
  BankCreatePayload,
  BankListReadModel,
  BankReadModel,
  DashboardReadModel,
  HoldingCreatePayload,
  HoldingReadModel,
  HoldingUpdatePayload,
  InstrumentSearchResult,
  PersonCreatePayload,
  PersonDetailReadModel,
  PersonBankAssignmentReadModel,
  PersonListReadModel,
  PersonQueryParams,
  PersonReadModel,
  PersonUpdatePayload,
  PortfolioCreatePayload,
  PortfolioDetailReadModel,
  PortfolioListReadModel,
  PortfolioReadModel,
  TaxAllowanceReadModel
} from '../types/models'

export const apiClient = {
  async persons(params?: PersonQueryParams) {
    return (await http.get<ApiEnvelope<PersonListReadModel>>('/app/persons', { params })).data.data
  },
  async createPerson(payload: PersonCreatePayload) {
    return (await http.post<ApiEnvelope<PersonReadModel>>('/app/persons', payload)).data.data
  },
  async person(personId: string) {
    return (await http.get<ApiEnvelope<PersonDetailReadModel>>(`/app/persons/${personId}`)).data.data
  },
  async updatePerson(personId: string, payload: PersonUpdatePayload) {
    return (await http.patch<ApiEnvelope<PersonReadModel>>(`/app/persons/${personId}`, payload)).data.data
  },
  async deletePerson(personId: string) { await http.delete(`/app/persons/${personId}`) },
  async personBanks(personId: string) { return (await http.get<ApiEnvelope<AssignmentListReadModel>>(`/app/persons/${personId}/banks`)).data.data },
  async assignBank(personId: string, bankId: string) { return (await http.post<ApiEnvelope<PersonBankAssignmentReadModel>>(`/app/persons/${personId}/banks/${bankId}`)).data.data },
  async unassignBank(personId: string, bankId: string) { await http.delete(`/app/persons/${personId}/banks/${bankId}`) },
  async allowances(personId: string, taxYear: number) {
    return (await http.get<ApiEnvelope<AllowanceListReadModel>>(`/app/persons/${personId}/allowances`, { params: { tax_year: taxYear } })).data.data
  },
  async setAllowance(personId: string, bankId: string, payload: AllowanceUpsertPayload) {
    return (await http.put<ApiEnvelope<TaxAllowanceReadModel>>(`/app/persons/${personId}/allowances/${bankId}`, payload)).data.data
  },
  async allowanceSummary(personId: string, taxYear: number) {
    return (await http.get<ApiEnvelope<AllowanceSummaryReadModel>>(`/app/persons/${personId}/allowances/summary`, { params: { tax_year: taxYear } })).data.data
  },
  async banks() { return (await http.get<ApiEnvelope<BankListReadModel>>('/app/banks')).data.data },
  async createBank(payload: BankCreatePayload) { return (await http.post<ApiEnvelope<BankReadModel>>('/app/banks', payload)).data.data },
  async dashboard(personId: string) { return (await http.get<ApiEnvelope<DashboardReadModel>>(`/app/persons/${personId}/dashboard`)).data.data },
  async accounts(personId: string) { return (await http.get<ApiEnvelope<AccountReadModel[]>>(`/app/persons/${personId}/accounts`)).data.data },
  async createAccount(personId: string, payload: AccountCreatePayload) { return (await http.post<ApiEnvelope<AccountReadModel>>(`/app/persons/${personId}/accounts`, payload)).data.data },
  async updateAccount(personId: string, accountId: string, payload: AccountUpdatePayload) { return (await http.patch<ApiEnvelope<AccountReadModel>>(`/app/persons/${personId}/accounts/${accountId}`, payload)).data.data },

  async portfolios(personId: string) {
    return (await http.get<ApiEnvelope<PortfolioListReadModel>>(`/app/persons/${personId}/portfolios`)).data.data
  },
  async createPortfolio(personId: string, payload: PortfolioCreatePayload) {
    return (await http.post<ApiEnvelope<PortfolioReadModel>>(`/app/persons/${personId}/portfolios`, payload)).data.data
  },
  async portfolio(portfolioId: string) {
    return (await http.get<ApiEnvelope<PortfolioDetailReadModel>>(`/app/portfolios/${portfolioId}`)).data.data
  },
  async addHolding(portfolioId: string, payload: HoldingCreatePayload) {
    return (await http.post<ApiEnvelope<HoldingReadModel>>(`/app/portfolios/${portfolioId}/holdings`, payload)).data.data
  },
  async updateHolding(portfolioId: string, holdingId: string, payload: HoldingUpdatePayload) {
    return (await http.patch<ApiEnvelope<HoldingReadModel>>(`/app/portfolios/${portfolioId}/holdings/${holdingId}`, payload)).data.data
  },
  async deleteHolding(portfolioId: string, holdingId: string) {
    await http.delete(`/app/portfolios/${portfolioId}/holdings/${holdingId}`)
  },
  async searchInstruments(q: string, limit = 10) {
    return (await http.get<ApiEnvelope<InstrumentSearchResult>>('/app/marketdata/instruments/search', { params: { q, limit } })).data.data
  }
}
