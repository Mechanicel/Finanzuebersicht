import { http } from '@/shared/api/http'
import type {
  ApiEnvelope,
  HoldingCreatePayload,
  HoldingReadModel,
  HoldingUpdatePayload,
  InstrumentSearchResult,
  PortfolioCreatePayload,
  PortfolioDetailReadModel,
  PortfolioListReadModel,
  PortfolioReadModel
} from '@/shared/model/types'

export async function fetchPortfolios(personId: string) {
  return (await http.get<ApiEnvelope<PortfolioListReadModel>>(`/app/persons/${personId}/portfolios`)).data.data
}

export async function createPortfolio(personId: string, payload: PortfolioCreatePayload) {
  return (await http.post<ApiEnvelope<PortfolioReadModel>>(`/app/persons/${personId}/portfolios`, payload)).data.data
}

export async function fetchPortfolio(portfolioId: string) {
  return (await http.get<ApiEnvelope<PortfolioDetailReadModel>>(`/app/portfolios/${portfolioId}`)).data.data
}

export async function addHolding(portfolioId: string, payload: HoldingCreatePayload) {
  return (await http.post<ApiEnvelope<HoldingReadModel>>(`/app/portfolios/${portfolioId}/holdings`, payload)).data.data
}

export async function updateHolding(portfolioId: string, holdingId: string, payload: HoldingUpdatePayload) {
  return (await http.patch<ApiEnvelope<HoldingReadModel>>(`/app/portfolios/${portfolioId}/holdings/${holdingId}`, payload)).data.data
}

export async function deleteHolding(portfolioId: string, holdingId: string) {
  await http.delete(`/app/portfolios/${portfolioId}/holdings/${holdingId}`)
}

export async function searchInstruments(q: string, limit = 10) {
  return (await http.get<ApiEnvelope<InstrumentSearchResult>>('/app/marketdata/instruments/search', { params: { q, limit } })).data.data
}
