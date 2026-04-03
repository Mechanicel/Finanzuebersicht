import { fetchDashboard } from '@/modules/dashboard/api/dashboardApi'
import { fetchPersons, createPerson, fetchPerson, updatePerson, deletePerson } from '@/modules/persons/api/personsApi'
import { fetchPersonBanks, assignBank, unassignBank, fetchBanks, createBank } from '@/modules/banks/api/banksApi'
import { fetchAllowances, setAllowance, fetchAllowanceSummary } from '@/modules/allowances/api/allowancesApi'
import { fetchAccounts, createAccount, updateAccount, deleteAccount } from '@/modules/accounts/api/accountsApi'
import {
  fetchPortfolios,
  createPortfolio,
  fetchPortfolio,
  addHolding,
  refreshHoldingPrices,
  updateHolding,
  deleteHolding,
  searchInstruments,
  marketdataProfile,
  refreshInstrumentPrice
} from '@/modules/portfolio/api/portfolioApi'

export const apiClient = {
  persons: fetchPersons,
  createPerson,
  person: fetchPerson,
  updatePerson,
  deletePerson,
  personBanks: fetchPersonBanks,
  assignBank,
  unassignBank,
  allowances: fetchAllowances,
  setAllowance,
  allowanceSummary: fetchAllowanceSummary,
  banks: fetchBanks,
  createBank,
  dashboard: fetchDashboard,
  accounts: fetchAccounts,
  createAccount,
  updateAccount,
  deleteAccount,
  portfolios: fetchPortfolios,
  createPortfolio,
  portfolio: fetchPortfolio,
  addHolding,
  refreshHoldingPrices,
  updateHolding,
  deleteHolding,
  searchInstruments,
  marketdataProfile,
  refreshInstrumentPrice
}
