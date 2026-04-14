import { http } from '@/shared/api/http'
import type {
  ApiEnvelope,
  AssignmentListReadModel,
  BankCreatePayload,
  BankListReadModel,
  BankReadModel,
  PersonBankAssignmentReadModel
} from '@/shared/model/types'

export async function fetchPersonBanks(personId: string) {
  return (await http.get<ApiEnvelope<AssignmentListReadModel>>(`/app/persons/${personId}/banks`)).data.data
}

export async function assignBank(personId: string, bankId: string) {
  return (await http.post<ApiEnvelope<PersonBankAssignmentReadModel>>(`/app/persons/${personId}/banks/${bankId}`)).data.data
}

export async function unassignBank(personId: string, bankId: string) {
  await http.delete(`/app/persons/${personId}/banks/${bankId}`)
}

export async function fetchBanks() {
  return (await http.get<ApiEnvelope<BankListReadModel>>('/app/banks')).data.data
}

export async function createBank(payload: BankCreatePayload) {
  return (await http.post<ApiEnvelope<BankReadModel>>('/app/banks', payload)).data.data
}
