import { http } from '@/shared/api/http'
import type {
  ApiEnvelope,
  HoldingCreatePayload,
  HoldingReadModel,
  HoldingsRefreshStubResponse,
  HoldingUpdatePayload,
  MarketdataProfile,
  InstrumentSearchResult,
  InstrumentHistoryRange,
  InstrumentHistoryResponse,
  InstrumentPriceRefreshResponse,
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

export async function fetchDepotAccountPortfolio(personId: string, accountId: string) {
  return (await http.get<ApiEnvelope<PortfolioReadModel>>(`/app/persons/${personId}/accounts/${accountId}/portfolio`)).data.data
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

export async function refreshHoldingPrices(portfolioId: string) {
  return (
    await http.post<ApiEnvelope<HoldingsRefreshStubResponse>>(`/app/portfolios/${portfolioId}/holdings/refresh-current-prices`)
  ).data.data
}

export async function searchInstruments(q: string, limit = 10) {
  return (await http.get<ApiEnvelope<InstrumentSearchResult>>('/app/marketdata/instruments/search', { params: { q, limit } })).data.data
}

export async function marketdataProfile(symbol: string) {
  return (await http.get<ApiEnvelope<MarketdataProfile>>(`/app/marketdata/instruments/${symbol}/profile`)).data.data
}

export async function refreshInstrumentPrice(symbol: string) {
  return (await http.post<ApiEnvelope<InstrumentPriceRefreshResponse>>(`/app/marketdata/instruments/${symbol}/refresh-price`)).data.data
}


export async function instrumentHistory(symbol: string, range: InstrumentHistoryRange = 'max') {
  return (
    await http.get<ApiEnvelope<InstrumentHistoryResponse>>(`/app/marketdata/instruments/${symbol}/history`, {
      params: { range }
    })
  ).data.data
}
