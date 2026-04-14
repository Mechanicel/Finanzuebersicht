import { http } from '@/shared/api/http'
import type {
  AllowanceListReadModel,
  AllowanceSummaryReadModel,
  AllowanceUpsertPayload,
  ApiEnvelope,
  TaxAllowanceReadModel
} from '@/shared/model/types'

export async function fetchAllowances(personId: string, taxYear: number) {
  return (await http.get<ApiEnvelope<AllowanceListReadModel>>(`/app/persons/${personId}/allowances`, { params: { tax_year: taxYear } })).data.data
}

export async function setAllowance(personId: string, bankId: string, payload: AllowanceUpsertPayload) {
  return (await http.put<ApiEnvelope<TaxAllowanceReadModel>>(`/app/persons/${personId}/allowances/${bankId}`, payload)).data.data
}

export async function fetchAllowanceSummary(personId: string, taxYear: number) {
  return (await http.get<ApiEnvelope<AllowanceSummaryReadModel>>(`/app/persons/${personId}/allowances/summary`, { params: { tax_year: taxYear } })).data.data
}
