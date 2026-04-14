import type { AccountReadModel, HoldingReadModel, PortfolioDetailReadModel, PortfolioReadModel } from '@/shared/model/types'

export type DepotAccountSummary = {
  accountId: string
  accountLabel: string
  bankName: string
  depotNumber: string | null
  portfolioId: string | null
  hasPortfolio: boolean
  holdingsCount: number
  investedTotal: number
  currency: string
  firstBuyDate: string | null
}

type SummaryInput = {
  account: AccountReadModel
  bankName: string
  portfolio: PortfolioReadModel | null
  portfolioDetail: PortfolioDetailReadModel | null
}

function fallbackSummary(account: AccountReadModel, bankName: string): DepotAccountSummary {
  return {
    accountId: account.account_id,
    accountLabel: account.label,
    bankName,
    depotNumber: account.depot_number ?? null,
    portfolioId: null,
    hasPortfolio: false,
    holdingsCount: 0,
    investedTotal: 0,
    currency: account.currency,
    firstBuyDate: null
  }
}

function investedTotal(holdings: HoldingReadModel[]): number {
  return holdings.reduce((sum, holding) => sum + holding.quantity * holding.acquisition_price, 0)
}

function firstBuyDate(holdings: HoldingReadModel[]): string | null {
  if (!holdings.length) {
    return null
  }

  return holdings.reduce((earliest, holding) => (holding.buy_date < earliest ? holding.buy_date : earliest), holdings[0].buy_date)
}

export function buildDepotAccountSummary({ account, bankName, portfolio, portfolioDetail }: SummaryInput): DepotAccountSummary {
  if (!portfolio || !portfolioDetail) {
    return fallbackSummary(account, bankName)
  }

  const holdings = portfolioDetail.holdings
  return {
    accountId: account.account_id,
    accountLabel: account.label,
    bankName,
    depotNumber: account.depot_number ?? null,
    portfolioId: portfolio.portfolio_id,
    hasPortfolio: true,
    holdingsCount: holdings.length,
    investedTotal: investedTotal(holdings),
    currency: holdings[0]?.currency ?? account.currency,
    firstBuyDate: firstBuyDate(holdings)
  }
}
