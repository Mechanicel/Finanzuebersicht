import { http } from '@/shared/api/http'
import type {
  AccountCreatePayload,
  AccountReadModel,
  AccountUpdatePayload,
  ApiEnvelope
} from '@/shared/model/types'

export async function fetchAccounts(personId: string) {
  return (await http.get<ApiEnvelope<AccountReadModel[]>>(`/app/persons/${personId}/accounts`)).data.data
}

export async function createAccount(personId: string, payload: AccountCreatePayload) {
  return (await http.post<ApiEnvelope<AccountReadModel>>(`/app/persons/${personId}/accounts`, payload)).data.data
}

export async function updateAccount(personId: string, accountId: string, payload: AccountUpdatePayload) {
  return (await http.patch<ApiEnvelope<AccountReadModel>>(`/app/persons/${personId}/accounts/${accountId}`, payload)).data.data
}

export async function deleteAccount(personId: string, accountId: string) {
  await http.delete(`/app/persons/${personId}/accounts/${accountId}`)
}
