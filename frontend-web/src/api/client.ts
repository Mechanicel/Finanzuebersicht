import { http } from './http'
import type {
  AccountReadModel,
  ApiEnvelope,
  DashboardReadModel,
  PersonCreatePayload,
  PersonDetailReadModel,
  PersonListReadModel,
  PersonQueryParams,
  PersonReadModel,
  PersonUpdatePayload,
  PortfolioReadModel
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
  async deletePerson(personId: string) {
    await http.delete(`/app/persons/${personId}`)
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
