import { http } from './http'
import type { AccountReadModel, ApiEnvelope, DashboardReadModel, PersonListReadModel, PortfolioReadModel } from '../types/models'

export const apiClient = {
  async persons() {
    return (await http.get<ApiEnvelope<PersonListReadModel>>('/app/persons')).data.data
  },
  async dashboard(personId: string) {
    return (await http.get<ApiEnvelope<DashboardReadModel>>(`/app/persons/${personId}/dashboard`)).data.data
  },
  async accounts(personId: string) {
    return (await http.get<ApiEnvelope<AccountReadModel[]>>(`/app/persons/${personId}/accounts`)).data.data
  },
  async portfolios(personId: string) {
    return (await http.get<ApiEnvelope<PortfolioReadModel[]>>(`/app/persons/${personId}/portfolios`)).data.data
  }
}
