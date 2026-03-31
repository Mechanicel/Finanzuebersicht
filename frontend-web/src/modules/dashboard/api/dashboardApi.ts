import { http } from '@/shared/api/http'
import type { ApiEnvelope, DashboardReadModel } from '@/shared/model/types'

export async function fetchDashboard(personId: string) {
  return (await http.get<ApiEnvelope<DashboardReadModel>>(`/app/persons/${personId}/dashboard`)).data.data
}
