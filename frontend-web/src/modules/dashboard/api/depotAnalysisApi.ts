import { http } from '@/shared/api/http'
import type {
  ApiEnvelope,
  DepotInstrumentBenchmarkCatalog,
  DepotInstrumentBenchmarkSearchResult,
  DepotInstrumentBenchmarkSummary,
  DepotInstrumentFinancials,
  DepotInstrumentFundamentals,
  DepotInstrumentRisk,
  DepotInstrumentTimeseries,
  DepotMarketdataHoldingsSummary,
  EtfData,
  PortfolioDetailReadModel,
  PortfolioListReadModel
} from '@/shared/model/types'

export async function fetchPersonPortfolios(personId: string) {
  return (await http.get<ApiEnvelope<PortfolioListReadModel>>(`/app/persons/${personId}/portfolios`)).data.data
}

export async function fetchPortfolioDetails(portfolioId: string) {
  return (await http.get<ApiEnvelope<PortfolioDetailReadModel>>(`/app/portfolios/${portfolioId}`)).data.data
}

export async function fetchHoldingsSummary(symbols: string[]) {
  const normalizedSymbols = symbols.map((symbol) => symbol.trim().toUpperCase()).filter(Boolean)
  if (normalizedSymbols.length === 0) {
    return { items: [], total: 0, source: 'empty_selection' } satisfies DepotMarketdataHoldingsSummary
  }

  return (
    await http.get<ApiEnvelope<DepotMarketdataHoldingsSummary>>('/app/marketdata/depot/holdings-summary', {
      params: { symbols: normalizedSymbols.join(',') }
    })
  ).data.data
}

export async function fetchInstrumentTimeseries(symbol: string, series: string, benchmark?: string) {
  return (
    await http.get<ApiEnvelope<DepotInstrumentTimeseries>>(`/app/marketdata/instruments/${symbol}/timeseries`, {
      params: { series, benchmark }
    })
  ).data.data
}

export async function fetchInstrumentRisk(symbol: string, benchmark?: string) {
  return (
    await http.get<ApiEnvelope<DepotInstrumentRisk>>(`/app/marketdata/instruments/${symbol}/risk`, {
      params: { benchmark }
    })
  ).data.data
}

export async function fetchInstrumentBenchmark(symbol: string, benchmark?: string) {
  return (
    await http.get<ApiEnvelope<DepotInstrumentBenchmarkSummary>>(`/app/marketdata/instruments/${symbol}/benchmark`, {
      params: { benchmark }
    })
  ).data.data
}

export async function fetchBenchmarkCatalog() {
  return (await http.get<ApiEnvelope<DepotInstrumentBenchmarkCatalog>>('/app/marketdata/benchmark-catalog')).data.data
}

export async function searchBenchmarkCatalog(query: string) {
  return (
    await http.get<ApiEnvelope<DepotInstrumentBenchmarkSearchResult>>('/app/marketdata/benchmark-search', {
      params: { q: query }
    })
  ).data.data
}

export async function fetchInstrumentFundamentals(symbol: string) {
  return (await http.get<ApiEnvelope<DepotInstrumentFundamentals>>(`/app/marketdata/instruments/${symbol}/fundamentals`)).data.data
}

export async function fetchInstrumentFinancials(symbol: string, period: 'annual' | 'quarterly' = 'annual') {
  return (
    await http.get<ApiEnvelope<DepotInstrumentFinancials>>(`/app/marketdata/instruments/${symbol}/financials`, {
      params: { period }
    })
  ).data.data
}

export async function fetchInstrumentEtfData(symbol: string) {
  return (await http.get<ApiEnvelope<EtfData>>(`/app/marketdata/instruments/${symbol}/etf-data`)).data.data
}
