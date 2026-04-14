import { http } from '@/shared/api/http'
import type {
  ApiEnvelope,
  DashboardAllocationPayload,
  DashboardMetricsPayload,
  DashboardOverviewPayload,
  DashboardSectionReadModel,
  DashboardTimeseriesPayload,
  DashboardReadModel
} from '@/shared/model/types'

export async function fetchDashboard(personId: string) {
  return (await http.get<ApiEnvelope<DashboardReadModel>>(`/app/persons/${personId}/dashboard`)).data.data
}

export async function fetchDashboardOverview(personId: string) {
  return (
    await http.get<ApiEnvelope<DashboardSectionReadModel<DashboardOverviewPayload>>>(
      `/app/persons/${personId}/dashboard/overview`
    )
  ).data.data
}

export async function fetchDashboardAllocation(personId: string) {
  return (
    await http.get<ApiEnvelope<DashboardSectionReadModel<DashboardAllocationPayload>>>(
      `/app/persons/${personId}/dashboard/allocation`
    )
  ).data.data
}

export async function fetchDashboardTimeseries(personId: string) {
  return (
    await http.get<ApiEnvelope<DashboardSectionReadModel<DashboardTimeseriesPayload>>>(
      `/app/persons/${personId}/dashboard/timeseries`
    )
  ).data.data
}

export async function fetchDashboardMetrics(personId: string) {
  return (
    await http.get<ApiEnvelope<DashboardSectionReadModel<DashboardMetricsPayload>>>(
      `/app/persons/${personId}/dashboard/metrics`
    )
  ).data.data
}
