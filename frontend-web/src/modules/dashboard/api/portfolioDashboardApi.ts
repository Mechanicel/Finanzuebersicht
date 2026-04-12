import { http } from '@/shared/api/http'
import type {
  ApiEnvelope,
  PortfolioAttributionReadModel,
  PortfolioDashboardRange,
  PortfolioContributorsReadModel,
  PortfolioDashboardReadModel,
  PortfolioDataCoverageReadModel,
  PortfolioExposuresReadModel,
  PortfolioHoldingsReadModel,
  PortfolioPerformanceReadModel,
  PortfolioRiskReadModel,
  PortfolioSummaryReadModel
} from '@/shared/model/types'

export async function fetchPortfolioSummary(personId: string) {
  return (await http.get<ApiEnvelope<PortfolioSummaryReadModel>>(`/app/persons/${personId}/portfolio-summary`)).data.data
}

export async function fetchPortfolioDashboard(personId: string, range: PortfolioDashboardRange | string = '3m') {
  return (
    await http.get<ApiEnvelope<PortfolioDashboardReadModel>>(`/app/persons/${personId}/portfolio-dashboard`, {
      params: { range }
    })
  ).data.data
}

export async function fetchPortfolioPerformance(personId: string) {
  return (
    await http.get<ApiEnvelope<PortfolioPerformanceReadModel>>(`/app/persons/${personId}/portfolio-performance`)
  ).data.data
}

export async function fetchPortfolioExposures(personId: string) {
  return (
    await http.get<ApiEnvelope<PortfolioExposuresReadModel>>(`/app/persons/${personId}/portfolio-exposures`)
  ).data.data
}

export async function fetchPortfolioHoldings(personId: string) {
  return (
    await http.get<ApiEnvelope<PortfolioHoldingsReadModel>>(`/app/persons/${personId}/portfolio-holdings`)
  ).data.data
}

export async function fetchPortfolioRisk(personId: string) {
  return (await http.get<ApiEnvelope<PortfolioRiskReadModel>>(`/app/persons/${personId}/portfolio-risk`)).data.data
}

export async function fetchPortfolioContributors(personId: string) {
  return (
    await http.get<ApiEnvelope<PortfolioContributorsReadModel>>(`/app/persons/${personId}/portfolio-contributors`)
  ).data.data
}

export async function fetchPortfolioAttribution(personId: string, range: PortfolioDashboardRange | string = '3m') {
  return (
    await http.get<ApiEnvelope<PortfolioAttributionReadModel>>(`/app/persons/${personId}/portfolio-attribution`, {
      params: { range }
    })
  ).data.data
}

export async function fetchPortfolioDataCoverage(personId: string) {
  return (
    await http.get<ApiEnvelope<PortfolioDataCoverageReadModel>>(`/app/persons/${personId}/portfolio-data-coverage`)
  ).data.data
}
