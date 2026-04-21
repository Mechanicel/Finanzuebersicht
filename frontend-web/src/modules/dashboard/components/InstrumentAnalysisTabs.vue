<template>
  <section class="tabs-root">
    <header class="tabs-head">
      <h4>
        Instrument-Analyse
        <span v-if="instrumentTypeBadge" class="type-badge" :class="instrumentTypeBadgeClass">
          {{ instrumentTypeBadge }}
        </span>
      </h4>
      <p v-if="selectedSymbol">Aktives Instrument: <strong>{{ selectedSymbol }}</strong></p>
      <p v-else>Wähle links ein Instrument, um Detailanalysen zu laden.</p>
    </header>

    <div class="tab-nav">
      <button
        v-for="tab in visibleTabs"
        :key="tab.key"
        type="button"
        class="tab-btn"
        :class="{ active: activeTab === tab.key }"
        @click="activeTab = tab.key"
      >
        {{ tab.label }}
      </button>
    </div>

    <EmptyState v-if="!selectedSymbol">Noch kein Instrument ausgewählt.</EmptyState>

    <template v-else>
      <div v-if="warnings.length" class="warning-box">
        <p v-for="warning in warnings" :key="warning">&#9888; {{ warning }}</p>
      </div>

      <LoadingState v-if="loading" />

      <template v-else>
        <!-- UEBERBLICK -->
        <article v-if="activeTab === 'overview'" class="card content-card">
          <h5>Überblick</h5>
          <dl class="kv-grid">
            <template v-for="item in overviewPairs" :key="item.key">
              <dt :title="item.tooltip ?? undefined">{{ item.key }}{{ item.tooltip ? ' ℹ' : '' }}</dt>
              <dd>{{ item.value }}</dd>
            </template>
          </dl>
        </article>

        <!-- KURS & RENDITE -->
        <article v-else-if="activeTab === 'returns'" class="card content-card">
          <div class="row-between">
            <h5>Kurs & Rendite</h5>
            <label>
              Benchmark
              <input v-model="benchmarkInput" class="input" placeholder="z. B. SPY" @change="applyBenchmark" />
            </label>
          </div>

          <div class="series-select">
            <button v-for="series in timeseriesSeries" :key="series" class="chip" @click="loadTimeseries(series)">
              {{ series }}
            </button>
          </div>

          <div v-if="chartPoints.length" class="chart-box">
            <SimpleLineChart :points="chartPoints" />
          </div>
          <EmptyState v-else>Keine Zeitreihendaten für die gewählte Serie.</EmptyState>
        </article>

        <!-- RISIKO & BENCHMARK -->
        <article v-else-if="activeTab === 'risk'" class="card content-card">
          <div class="row-between">
            <h5>Risiko & Benchmark</h5>
            <button type="button" class="btn small" @click="reloadRisk">Aktualisieren</button>
          </div>
          <dl class="kv-grid">
            <dt :title="GLOSSARY.beta">Volatilität Instrument ℹ</dt>
            <dd>{{ fmtRatio(risk?.volatility_proxy) }}</dd>
            <dt>Volatilität Benchmark</dt>
            <dd>{{ fmtRatio(risk?.benchmark_volatility_proxy) }}</dd>
            <dt>Datenpunkte (aligned)</dt>
            <dd>{{ risk?.aligned_points ?? 0 }}</dd>
          </dl>

          <h6>Benchmark-Katalog</h6>
          <ul class="list">
            <li v-for="item in benchmarkCatalog.items" :key="item.symbol">
              <button type="button" class="link-btn" @click="selectBenchmark(item.symbol)">{{ item.symbol }} – {{ item.name }}</button>
            </li>
          </ul>

          <h6>Freie Vergleichssuche</h6>
          <div class="inline-row">
            <input v-model="searchTerm" class="input" placeholder="Name oder Symbol" />
            <button type="button" class="btn small" @click="searchBenchmark">Suchen</button>
          </div>
          <ul class="list" v-if="benchmarkSearch.items.length">
            <li v-for="item in benchmarkSearch.items" :key="`${item.symbol}-${item.name}`">
              {{ item.symbol }} – {{ item.name }}
            </li>
          </ul>
        </article>

        <!-- FUNDAMENTALS -->
        <article v-else-if="activeTab === 'fundamentals'" class="card content-card">
          <h5>Fundamentals</h5>

          <!-- Bewertungskennzahlen -->
          <section v-if="isEquity" class="fund-section">
            <h6>Bewertung</h6>
            <dl class="kv-grid">
              <dt :title="GLOSSARY.marketCap">Marktkapitalisierung ℹ</dt>
              <dd>{{ fmtLarge(fundamentals?.market_cap) }}</dd>
              <dt :title="GLOSSARY.enterpriseValue">Unternehmenswert (EV) ℹ</dt>
              <dd>{{ fmtLarge(fundamentals?.enterprise_value) }}</dd>
              <dt :title="GLOSSARY.trailingPe">KGV (trailing) ℹ</dt>
              <dd>{{ fmtRatio(fundamentals?.trailing_pe) }}</dd>
              <dt :title="GLOSSARY.forwardPe">KGV (forward) ℹ</dt>
              <dd>{{ fmtRatio(fundamentals?.forward_pe) }}</dd>
              <dt :title="GLOSSARY.priceToBook">Kurs-Buchwert (KBV) ℹ</dt>
              <dd>{{ fmtRatio(fundamentals?.price_to_book) }}</dd>
              <dt :title="GLOSSARY.dividendYield">Dividendenrendite ℹ</dt>
              <dd>{{ fmtPercent(fundamentals?.dividend_yield) }}</dd>
              <dt :title="GLOSSARY.beta">Beta ℹ</dt>
              <dd>{{ fmtRatio(fundamentals?.beta) }}</dd>
            </dl>
          </section>

          <!-- Rentabilität -->
          <section v-if="isEquity" class="fund-section">
            <h6>Rentabilität</h6>
            <dl class="kv-grid">
              <dt :title="GLOSSARY.grossMargin">Bruttomarge ℹ</dt>
              <dd>{{ fmtPercent(fundamentals?.gross_margins) }}</dd>
              <dt :title="GLOSSARY.operatingMargin">Operative Marge ℹ</dt>
              <dd>{{ fmtPercent(fundamentals?.operating_margins) }}</dd>
              <dt :title="GLOSSARY.netMargin">Nettomarge ℹ</dt>
              <dd>{{ fmtPercent(fundamentals?.profit_margins) }}</dd>
              <dt :title="GLOSSARY.roe">ROE ℹ</dt>
              <dd>{{ fmtPercent(fundamentals?.return_on_equity) }}</dd>
              <dt :title="GLOSSARY.roa">ROA ℹ</dt>
              <dd>{{ fmtPercent(fundamentals?.return_on_assets) }}</dd>
              <dt :title="GLOSSARY.debtToEquity">Verschuldungsgrad (D/E) ℹ</dt>
              <dd>{{ fmtRatio(fundamentals?.debt_to_equity) }}</dd>
              <dt :title="GLOSSARY.currentRatio">Current Ratio ℹ</dt>
              <dd>{{ fmtRatio(fundamentals?.current_ratio) }}</dd>
            </dl>
          </section>

          <!-- ETF-Übersicht -->
          <section v-if="isEtf" class="fund-section">
            <h6>ETF-Übersicht</h6>
            <dl class="kv-grid">
              <dt :title="GLOSSARY.aum">Fondsvolumen (AUM) ℹ</dt>
              <dd>{{ fmtLarge(fundamentals?.total_assets_aum) }}</dd>
              <dt :title="GLOSSARY.fundFamily">Fondsgesellschaft ℹ</dt>
              <dd>{{ fundamentals?.fund_family ?? '—' }}</dd>
              <dt :title="GLOSSARY.inceptionDate">Auflagedatum ℹ</dt>
              <dd>{{ fundamentals?.fund_inception_date ?? '—' }}</dd>
              <dt :title="GLOSSARY.fundYield">Ausschüttungsrendite ℹ</dt>
              <dd>{{ fmtPercent(fundamentals?.fund_yield) }}</dd>
              <dt :title="GLOSSARY.ytdReturn">YTD-Rendite ℹ</dt>
              <dd>{{ fmtPercent(fundamentals?.ytd_return) }}</dd>
            </dl>
          </section>

          <!-- Unternehmensprofil -->
          <section class="fund-section">
            <h6>Profil</h6>
            <dl class="kv-grid">
              <dt>Name</dt>
              <dd>{{ fundamentals?.company_name ?? '—' }}</dd>
              <dt>Sektor</dt>
              <dd>{{ fundamentals?.sector ?? '—' }}</dd>
              <dt>Branche</dt>
              <dd>{{ fundamentals?.industry ?? '—' }}</dd>
              <dt>Land</dt>
              <dd>{{ fundamentals?.country ?? '—' }}</dd>
              <dt>Währung</dt>
              <dd>{{ fundamentals?.currency ?? '—' }}</dd>
              <dt>Website</dt>
              <dd>
                <a v-if="fundamentals?.website" :href="fundamentals.website" target="_blank" rel="noopener" class="ext-link">
                  {{ fundamentals.website }}
                </a>
                <span v-else>—</span>
              </dd>
            </dl>
            <p v-if="fundamentals?.description" class="description-text">{{ fundamentals.description }}</p>
          </section>
        </article>

        <!-- ETF-DETAILS -->
        <article v-else-if="activeTab === 'etf'" class="card content-card">
          <h5>ETF-Details</h5>

          <template v-if="etfData">
            <!-- Kennzahlen -->
            <section class="fund-section">
              <h6>Kennzahlen</h6>
              <dl class="kv-grid">
                <dt :title="GLOSSARY.aum">Fondsvolumen (AUM) ℹ</dt>
                <dd>{{ fmtLarge(etfData.aum) }}</dd>
                <dt :title="GLOSSARY.expenseRatio">Kostenquote (TER) ℹ</dt>
                <dd>{{ fmtPercent(etfData.expense_ratio) }}</dd>
                <dt :title="GLOSSARY.fundYield">Ausschüttungsrendite ℹ</dt>
                <dd>{{ fmtPercent(etfData.fund_yield) }}</dd>
                <dt :title="GLOSSARY.ytdReturn">YTD-Rendite ℹ</dt>
                <dd>{{ fmtPercent(etfData.ytd_return) }}</dd>
                <dt :title="GLOSSARY.threeYearReturn">3-Jahres-Rendite ℹ</dt>
                <dd>{{ fmtPercent(etfData.three_year_return) }}</dd>
                <dt :title="GLOSSARY.fiveYearReturn">5-Jahres-Rendite ℹ</dt>
                <dd>{{ fmtPercent(etfData.five_year_return) }}</dd>
                <dt :title="GLOSSARY.inceptionDate">Auflagedatum ℹ</dt>
                <dd>{{ etfData.inception_date ?? '—' }}</dd>
                <dt :title="GLOSSARY.fundFamily">Fondsgesellschaft ℹ</dt>
                <dd>{{ etfData.fund_family ?? '—' }}</dd>
                <dt>Rechtsform</dt>
                <dd>{{ etfData.legal_type ?? '—' }}</dd>
              </dl>
            </section>

            <!-- Top-Holdings -->
            <section v-if="etfData.top_holdings.length" class="fund-section">
              <h6 :title="GLOSSARY.topHoldings">Top-10-Positionen ℹ</h6>
              <table class="etf-table">
                <thead>
                  <tr>
                    <th>Symbol</th>
                    <th>Name</th>
                    <th>Gewicht</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="holding in etfData.top_holdings" :key="holding.symbol">
                    <td class="mono">{{ holding.symbol }}</td>
                    <td>{{ holding.name ?? '—' }}</td>
                    <td class="right">{{ fmtPercent(holding.weight) }}</td>
                  </tr>
                </tbody>
              </table>
            </section>

            <!-- Sektoraufteilung -->
            <section v-if="hasSectorWeights" class="fund-section">
              <h6 :title="GLOSSARY.sectorWeights">Sektoraufteilung ℹ</h6>
              <div class="bar-list">
                <div
                  v-for="(weight, sector) in sortedSectorWeights"
                  :key="sector"
                  class="bar-row"
                >
                  <span class="bar-label">{{ formatSectorName(String(sector)) }}</span>
                  <div class="bar-track">
                    <div class="bar-fill" :style="{ width: `${Math.min(weight * 100, 100)}%` }" />
                  </div>
                  <span class="bar-value">{{ fmtPercent(weight) }}</span>
                </div>
              </div>
            </section>

            <!-- Asset-Klassen -->
            <section v-if="hasAssetClasses" class="fund-section">
              <h6 :title="GLOSSARY.assetClasses">Asset-Klassen ℹ</h6>
              <dl class="kv-grid">
                <template v-for="(value, key) in etfData.asset_classes" :key="key">
                  <dt>{{ formatAssetClassName(String(key)) }}</dt>
                  <dd>{{ fmtPercent(value) }}</dd>
                </template>
              </dl>
            </section>
          </template>
          <EmptyState v-else>Keine ETF-Daten verfügbar.</EmptyState>
        </article>

        <!-- FINANZBERICHTE (nur für Aktien) -->
        <article v-else-if="activeTab === 'financials'" class="card content-card">
          <div class="row-between">
            <h5>Finanzberichte</h5>
            <select v-if="!isEtf" v-model="financialPeriod" class="input" @change="loadFinancials">
              <option value="annual">Annual</option>
              <option value="quarterly">Quarterly</option>
            </select>
          </div>

          <!-- ETF-Hinweis -->
          <div v-if="isEtf" class="etf-notice">
            <p>Dieses Instrument ist ein <strong>ETF/Fonds</strong>. Unternehmensabschlüsse existieren nicht.</p>
            <p>Details findest du im Tab <button type="button" class="link-btn" @click="activeTab = 'etf'">ETF-Details</button>.</p>
          </div>

          <template v-else>
            <p v-if="financialsSummaryText" class="financials-summary">{{ financialsSummaryText }}</p>

            <!-- Bilanz -->
            <template v-if="balanceSheetRows.length">
              <h6>Bilanz (Balance Sheet)</h6>
              <section class="period-chip-row">
                <button
                  v-for="row in balanceSheetRows"
                  :key="balanceSheetColumnTitle(row)"
                  type="button"
                  class="period-chip"
                  :class="{ active: selectedBalanceSheetPeriodKey === balanceSheetColumnTitle(row) }"
                  @click="selectedBalanceSheetPeriodKey = balanceSheetColumnTitle(row)"
                >
                  {{ balanceSheetColumnTitle(row) }}
                </button>
              </section>

              <section v-if="selectedBalanceSheetRow" class="financials-detail-card">
                <div class="stmt-group">
                  <h6 class="stmt-group-title">Vermögen</h6>
                  <dl class="kv-grid">
                    <dt :title="GLOSSARY.totalAssets">Bilanzsumme ℹ</dt>
                    <dd>{{ fmtMoney(selectedBalanceSheetRow.totalAssets, selectedBalanceSheetRow.reportedCurrency) }}</dd>
                    <dt :title="GLOSSARY.totalCurrentAssets">Kurzfristiges Umlaufvermögen ℹ</dt>
                    <dd>{{ fmtMoney(selectedBalanceSheetRow.totalCurrentAssets, selectedBalanceSheetRow.reportedCurrency) }}</dd>
                    <dt :title="GLOSSARY.cashAndCashEquivalents">Kassenbestand ℹ</dt>
                    <dd>{{ fmtMoney(selectedBalanceSheetRow.cashAndCashEquivalents, selectedBalanceSheetRow.reportedCurrency) }}</dd>
                    <dt :title="GLOSSARY.cashAndShortTermInvestments">Liquiditätsreserven ℹ</dt>
                    <dd>{{ fmtMoney(selectedBalanceSheetRow.cashAndShortTermInvestments, selectedBalanceSheetRow.reportedCurrency) }}</dd>
                    <dt :title="GLOSSARY.accountsReceivable">Forderungen ℹ</dt>
                    <dd>{{ fmtMoney(selectedBalanceSheetRow.accountsReceivable, selectedBalanceSheetRow.reportedCurrency) }}</dd>
                    <dt :title="GLOSSARY.inventory">Vorräte ℹ</dt>
                    <dd>{{ fmtMoney(selectedBalanceSheetRow.inventory, selectedBalanceSheetRow.reportedCurrency) }}</dd>
                    <dt :title="GLOSSARY.netPPE">Sachanlagen (netto) ℹ</dt>
                    <dd>{{ fmtMoney(selectedBalanceSheetRow.netPPE, selectedBalanceSheetRow.reportedCurrency) }}</dd>
                    <dt :title="GLOSSARY.goodwillAndIntangibles">Firmenwert & Immaterielles ℹ</dt>
                    <dd>{{ fmtMoney(selectedBalanceSheetRow.goodwillAndIntangibles, selectedBalanceSheetRow.reportedCurrency) }}</dd>
                  </dl>
                </div>
                <div class="stmt-group">
                  <h6 class="stmt-group-title">Verbindlichkeiten & Eigenkapital</h6>
                  <dl class="kv-grid">
                    <dt :title="GLOSSARY.totalLiabilities">Gesamtverbindlichkeiten ℹ</dt>
                    <dd>{{ fmtMoney(selectedBalanceSheetRow.totalLiabilities, selectedBalanceSheetRow.reportedCurrency) }}</dd>
                    <dt :title="GLOSSARY.totalCurrentLiabilities">Kurzfristige Verbindlichkeiten ℹ</dt>
                    <dd>{{ fmtMoney(selectedBalanceSheetRow.totalCurrentLiabilities, selectedBalanceSheetRow.reportedCurrency) }}</dd>
                    <dt :title="GLOSSARY.totalDebt">Gesamtschulden ℹ</dt>
                    <dd>{{ fmtMoney(selectedBalanceSheetRow.totalDebt, selectedBalanceSheetRow.reportedCurrency) }}</dd>
                    <dt :title="GLOSSARY.netDebt">Nettoverschuldung ℹ</dt>
                    <dd>{{ fmtMoney(selectedBalanceSheetRow.netDebt, selectedBalanceSheetRow.reportedCurrency) }}</dd>
                    <dt :title="GLOSSARY.accountsPayable">Verbindlichkeiten (Lieferanten) ℹ</dt>
                    <dd>{{ fmtMoney(selectedBalanceSheetRow.accountsPayable, selectedBalanceSheetRow.reportedCurrency) }}</dd>
                    <dt :title="GLOSSARY.totalEquity">Eigenkapital ℹ</dt>
                    <dd>{{ fmtMoney(selectedBalanceSheetRow.totalEquity, selectedBalanceSheetRow.reportedCurrency) }}</dd>
                    <dt :title="GLOSSARY.retainedEarnings">Gewinnrücklagen ℹ</dt>
                    <dd>{{ fmtMoney(selectedBalanceSheetRow.retainedEarnings, selectedBalanceSheetRow.reportedCurrency) }}</dd>
                    <dt :title="GLOSSARY.workingCapital">Working Capital ℹ</dt>
                    <dd>{{ fmtMoney(selectedBalanceSheetRow.workingCapital, selectedBalanceSheetRow.reportedCurrency) }}</dd>
                  </dl>
                </div>
              </section>

              <!-- Historische Kompaktübersicht Bilanz -->
              <section class="history-compact">
                <h6>Historischer Verlauf (Bilanz)</h6>
                <table class="financials-compact-table">
                  <thead>
                    <tr>
                      <th>Periode</th>
                      <th :title="GLOSSARY.totalAssets">Bilanzsumme ℹ</th>
                      <th :title="GLOSSARY.totalEquity">Eigenkapital ℹ</th>
                      <th :title="GLOSSARY.cashAndCashEquivalents">Cash ℹ</th>
                      <th :title="GLOSSARY.netDebt">Nettoverschuldung ℹ</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="row in balanceSheetRows" :key="`bs-${balanceSheetColumnTitle(row)}`">
                      <td>{{ row.date ?? '—' }}</td>
                      <td>{{ fmtMoney(row.totalAssets, row.reportedCurrency) }}</td>
                      <td>{{ fmtMoney(row.totalEquity, row.reportedCurrency) }}</td>
                      <td>{{ fmtMoney(row.cashAndCashEquivalents, row.reportedCurrency) }}</td>
                      <td>{{ fmtMoney(row.netDebt, row.reportedCurrency) }}</td>
                    </tr>
                  </tbody>
                </table>
              </section>
            </template>
            <EmptyState v-else>Keine Bilanzdaten verfügbar.</EmptyState>

            <!-- GuV -->
            <template v-if="incomeRows.length">
              <h6 class="section-title">Gewinn- und Verlustrechnung</h6>
              <section class="history-compact">
                <table class="financials-compact-table">
                  <thead>
                    <tr>
                      <th>Periode</th>
                      <th :title="GLOSSARY.revenue">Umsatz ℹ</th>
                      <th :title="GLOSSARY.grossProfit">Bruttogewinn ℹ</th>
                      <th :title="GLOSSARY.grossMargin">Bruttomarge ℹ</th>
                      <th :title="GLOSSARY.ebitda">EBITDA ℹ</th>
                      <th :title="GLOSSARY.netIncome">Jahresüberschuss ℹ</th>
                      <th :title="GLOSSARY.netMargin">Nettomarge ℹ</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="row in incomeRows" :key="`inc-${row.date}`">
                      <td>{{ row.date ?? '—' }}</td>
                      <td>{{ fmtMoney(row.revenue, financialCurrency) }}</td>
                      <td>{{ fmtMoney(row.grossProfit, financialCurrency) }}</td>
                      <td>{{ fmtPercent(row.grossMargin) }}</td>
                      <td>{{ fmtMoney(row.ebitda, financialCurrency) }}</td>
                      <td>{{ fmtMoney(row.netIncome, financialCurrency) }}</td>
                      <td>{{ fmtPercent(row.netMargin) }}</td>
                    </tr>
                  </tbody>
                </table>
              </section>
            </template>

            <!-- Cashflow -->
            <template v-if="cashFlowRows.length">
              <h6 class="section-title">Cashflow</h6>
              <section class="history-compact">
                <table class="financials-compact-table">
                  <thead>
                    <tr>
                      <th>Periode</th>
                      <th :title="GLOSSARY.operatingCashFlow">Operativer CF ℹ</th>
                      <th :title="GLOSSARY.capitalExpenditure">CapEx ℹ</th>
                      <th :title="GLOSSARY.freeCashFlow">Free CF ℹ</th>
                      <th :title="GLOSSARY.dividendsPaid">Dividenden ℹ</th>
                      <th :title="GLOSSARY.shareRepurchase">Rückkäufe ℹ</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="row in cashFlowRows" :key="`cf-${row.date}`">
                      <td>{{ row.date ?? '—' }}</td>
                      <td>{{ fmtMoney(row.operatingCashFlow, financialCurrency) }}</td>
                      <td>{{ fmtMoney(row.capitalExpenditure, financialCurrency) }}</td>
                      <td>{{ fmtMoney(row.freeCashFlow, financialCurrency) }}</td>
                      <td>{{ fmtMoney(row.dividendsPaid, financialCurrency) }}</td>
                      <td>{{ fmtMoney(row.shareRepurchase, financialCurrency) }}</td>
                    </tr>
                  </tbody>
                </table>
              </section>
            </template>

            <!-- Derived Ratios -->
            <template v-if="financials?.derived && Object.keys(financials.derived).length">
              <h6 class="section-title">Abgeleitete Kennzahlen (aktuellste Periode)</h6>
              <dl class="kv-grid derived-grid">
                <dt :title="GLOSSARY.roe">ROE ℹ</dt>
                <dd>{{ fmtPercent(financials.derived.roe) }}</dd>
                <dt :title="GLOSSARY.roa">ROA ℹ</dt>
                <dd>{{ fmtPercent(financials.derived.roa) }}</dd>
                <dt :title="GLOSSARY.debtToEquity">Verschuldungsgrad (D/E) ℹ</dt>
                <dd>{{ fmtRatio(financials.derived.debt_to_equity) }}</dd>
                <dt :title="GLOSSARY.currentRatio">Current Ratio ℹ</dt>
                <dd>{{ fmtRatio(financials.derived.current_ratio) }}</dd>
                <dt :title="GLOSSARY.grossMargin">Bruttomarge ℹ</dt>
                <dd>{{ fmtPercent(financials.derived.gross_margin) }}</dd>
                <dt :title="GLOSSARY.operatingMargin">Operative Marge ℹ</dt>
                <dd>{{ fmtPercent(financials.derived.operating_margin) }}</dd>
                <dt :title="GLOSSARY.netMargin">Nettomarge ℹ</dt>
                <dd>{{ fmtPercent(financials.derived.net_margin) }}</dd>
                <dt :title="GLOSSARY.freeCashFlow">Free Cashflow ℹ</dt>
                <dd>{{ fmtMoney(financials.derived.free_cash_flow, financialCurrency) }}</dd>
                <dt :title="GLOSSARY.netDebt">Nettoverschuldung ℹ</dt>
                <dd>{{ fmtMoney(financials.derived.net_debt, financialCurrency) }}</dd>
                <dt :title="GLOSSARY.ebitda">EBITDA ℹ</dt>
                <dd>{{ fmtMoney(financials.derived.ebitda, financialCurrency) }}</dd>
              </dl>
            </template>
          </template>
        </article>

        <!-- TECHNISCHE DETAILS -->
        <article v-else class="card content-card">
          <h5>Rohdaten</h5>
          <div class="blocks">
            <section class="block">
              <h6>Timeseries Meta</h6>
              <p>Serie: {{ timeseries?.series ?? 'n/a' }} | Benchmark: {{ timeseries?.benchmark_symbol ?? 'n/a' }}</p>
            </section>
            <section class="block">
              <h6>Risk Meta</h6>
              <p>Benchmark: {{ risk?.benchmark ?? 'n/a' }} | Aligned Points: {{ risk?.aligned_points ?? 0 }}</p>
            </section>
            <section class="block">
              <h6>Instrument-Typ</h6>
              <p>{{ instrumentType ?? 'Unbekannt' }}</p>
            </section>
          </div>
        </article>
      </template>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import {
  fetchBenchmarkCatalog,
  fetchInstrumentBenchmark,
  fetchInstrumentEtfData,
  fetchInstrumentFinancials,
  fetchInstrumentFundamentals,
  fetchInstrumentRisk,
  fetchInstrumentTimeseries,
  searchBenchmarkCatalog
} from '@/modules/dashboard/api/depotAnalysisApi'
import type {
  DepotInstrumentBenchmarkCatalog,
  DepotInstrumentBenchmarkSearchResult,
  DepotInstrumentBalanceSheetStatementRow,
  DepotInstrumentCashFlowRow,
  DepotInstrumentFinancials,
  DepotInstrumentFundamentals,
  DepotInstrumentIncomeStatementRow,
  DepotInstrumentRisk,
  DepotInstrumentTimeseries,
  EtfData,
  InstrumentType
} from '@/shared/model/types'
import { GLOSSARY } from '@/shared/ui/glossary'
import EmptyState from '@/shared/ui/EmptyState.vue'
import LoadingState from '@/shared/ui/LoadingState.vue'
import SimpleLineChart from '@/shared/ui/SimpleLineChart.vue'

const props = defineProps<{ selectedSymbol: string | null }>()

const ALL_TABS = [
  { key: 'overview', label: 'Überblick' },
  { key: 'returns', label: 'Kurs & Rendite' },
  { key: 'risk', label: 'Risiko & Benchmark' },
  { key: 'fundamentals', label: 'Fundamentals' },
  { key: 'etf', label: 'ETF-Details' },
  { key: 'financials', label: 'Finanzberichte' },
  { key: 'raw', label: 'Technische Details' }
] as const

type TabKey = (typeof ALL_TABS)[number]['key']

const timeseriesSeries = ['price', 'benchmark_price', 'returns', 'drawdown', 'benchmark_relative']
const activeTab = ref<TabKey>('overview')
const loading = ref(false)
const nonFinancialWarnings = ref<string[]>([])
const financialWarnings = ref<string[]>([])
const benchmarkAutoWarning = ref<string | null>(null)
const benchmarkInput = ref('SPY')
const searchTerm = ref('')
const financialPeriod = ref<'annual' | 'quarterly'>('annual')
const selectedBalanceSheetPeriodKey = ref('')
const selectedSeries = ref(timeseriesSeries[0])

const timeseries = ref<DepotInstrumentTimeseries | null>(null)
const risk = ref<DepotInstrumentRisk | null>(null)
const fundamentals = ref<DepotInstrumentFundamentals | null>(null)
const financials = ref<DepotInstrumentFinancials | null>(null)
const etfData = ref<EtfData | null>(null)
const benchmarkCatalog = ref<DepotInstrumentBenchmarkCatalog>({ items: [] })
const benchmarkSearch = ref<DepotInstrumentBenchmarkSearchResult>({ query: '', items: [], total: 0 })

// Instrument type detection
const instrumentType = computed<InstrumentType | null>(() => {
  return (fundamentals.value?.instrument_type ?? financials.value?.instrument_type ?? null) as InstrumentType | null
})
const isEtf = computed(() => instrumentType.value === 'ETF' || instrumentType.value === 'MUTUALFUND')
const isEquity = computed(() => !isEtf.value && instrumentType.value !== null)

// Tab visibility: hide ETF tab for non-ETFs, keep financials tab always
const visibleTabs = computed(() =>
  ALL_TABS.filter((tab) => {
    if (tab.key === 'etf') return isEtf.value
    return true
  })
)

const instrumentTypeBadge = computed(() => {
  if (!instrumentType.value) return null
  const labels: Record<InstrumentType, string> = {
    EQUITY: 'Aktie',
    ETF: 'ETF',
    MUTUALFUND: 'Fonds',
    INDEX: 'Index',
    UNKNOWN: ''
  }
  return labels[instrumentType.value] || null
})

const instrumentTypeBadgeClass = computed(() => ({
  'badge-etf': isEtf.value,
  'badge-equity': isEquity.value
}))

const warnings = computed(() => [...nonFinancialWarnings.value, ...financialWarnings.value])
const chartPoints = computed(() => timeseries.value?.instrument.points ?? [])

const financialCurrency = computed(() => financials.value?.currency ?? undefined)

const balanceSheetRows = computed<DepotInstrumentBalanceSheetStatementRow[]>(() => {
  const rawRows = financials.value?.statements?.balance_sheet ?? []
  return [...rawRows]
    .sort((a, b) => {
      const aDate = a?.date ? Date.parse(a.date) : NaN
      const bDate = b?.date ? Date.parse(b.date) : NaN
      if (isNaN(aDate) && isNaN(bDate)) return 0
      if (isNaN(aDate)) return 1
      if (isNaN(bDate)) return -1
      return bDate - aDate
    })
    .slice(0, 6)
})

const incomeRows = computed<DepotInstrumentIncomeStatementRow[]>(() => {
  const rawRows = (financials.value?.statements?.income_statement ?? []) as DepotInstrumentIncomeStatementRow[]
  return [...rawRows]
    .sort((a, b) => ((b?.date ?? '') > (a?.date ?? '') ? 1 : -1))
    .slice(0, 6)
})

const cashFlowRows = computed<DepotInstrumentCashFlowRow[]>(() => {
  const rawRows = (financials.value?.statements?.cash_flow ?? []) as DepotInstrumentCashFlowRow[]
  return [...rawRows]
    .sort((a, b) => ((b?.date ?? '') > (a?.date ?? '') ? 1 : -1))
    .slice(0, 6)
})

const hasSectorWeights = computed(() => etfData.value && Object.keys(etfData.value.sector_weights).length > 0)
const hasAssetClasses = computed(() => etfData.value && Object.keys(etfData.value.asset_classes).length > 0)

const sortedSectorWeights = computed(() => {
  if (!etfData.value) return {}
  const entries = Object.entries(etfData.value.sector_weights).sort(([, a], [, b]) => b - a)
  return Object.fromEntries(entries)
})

const financialsSummaryText = computed(() => {
  if (!financials.value) return ''
  const inc = financials.value.statements?.income_statement?.length ?? 0
  const bs = financials.value.statements?.balance_sheet?.length ?? 0
  const cf = financials.value.statements?.cash_flow?.length ?? 0
  return `GuV: ${inc} Perioden | Bilanz: ${bs} | Cashflow: ${cf}`
})

const selectedBalanceSheetRow = computed<DepotInstrumentBalanceSheetStatementRow | null>(() => {
  if (!balanceSheetRows.value.length) return null
  return (
    balanceSheetRows.value.find((row) => balanceSheetColumnTitle(row) === selectedBalanceSheetPeriodKey.value) ??
    balanceSheetRows.value[0]
  )
})

const overviewPairs = computed(() => [
  { key: 'Symbol', value: props.selectedSymbol ?? 'n/a', tooltip: null },
  { key: 'Typ', value: instrumentTypeBadge.value ?? 'Unbekannt', tooltip: null },
  { key: 'Benchmark', value: risk.value?.benchmark ?? benchmarkInput.value, tooltip: null },
  { key: 'Kursdatenpunkte', value: String(chartPoints.value.length), tooltip: null },
  { key: 'Warnungen', value: String(warnings.value.length), tooltip: null }
])

watch(
  () => props.selectedSymbol,
  (symbol) => {
    resetTabData()
    if (!symbol) return
    void loadActiveTabData()
  },
  { immediate: true }
)

watch(activeTab, () => {
  if (!props.selectedSymbol) return
  void loadActiveTabData()
})

watch(
  balanceSheetRows,
  (rows) => {
    if (!rows.length) {
      selectedBalanceSheetPeriodKey.value = ''
      return
    }
    if (!rows.some((row) => balanceSheetColumnTitle(row) === selectedBalanceSheetPeriodKey.value)) {
      selectedBalanceSheetPeriodKey.value = balanceSheetColumnTitle(rows[0])
    }
  },
  { immediate: true }
)

// When instrument type becomes known, switch ETF users away from financials to etf tab
watch(isEtf, (etf) => {
  if (etf && activeTab.value === 'financials') {
    activeTab.value = 'etf'
  }
})

function resetTabData() {
  nonFinancialWarnings.value = []
  financialWarnings.value = []
  benchmarkAutoWarning.value = null
  timeseries.value = null
  risk.value = null
  fundamentals.value = null
  financials.value = null
  etfData.value = null
  benchmarkCatalog.value = { items: [] }
  benchmarkSearch.value = { query: '', items: [], total: 0 }
  selectedSeries.value = timeseriesSeries[0]
}

function recomputeNonFinancialWarnings() {
  nonFinancialWarnings.value = [
    ...(timeseries.value?.meta?.warnings ?? []).map((entry) => entry.message),
    ...(risk.value?.meta?.warnings ?? []).map((entry) => entry.message),
    ...(benchmarkAutoWarning.value ? [benchmarkAutoWarning.value] : [])
  ]
}

async function withLoading(task: () => Promise<void>) {
  loading.value = true
  try {
    await task()
  } catch {
    nonFinancialWarnings.value = ['Einige Instrumentdaten konnten nicht geladen werden.']
    financialWarnings.value = []
  } finally {
    loading.value = false
  }
}

async function loadActiveTabData() {
  if (!props.selectedSymbol) return
  const symbol = props.selectedSymbol
  if (activeTab.value === 'overview') {
    await withLoading(async () => {
      await loadTimeseries(timeseriesSeries[0], false, symbol)
    })
    return
  }
  if (activeTab.value === 'returns') {
    await withLoading(async () => {
      await loadTimeseries(selectedSeries.value, false, symbol)
    })
    return
  }
  if (activeTab.value === 'risk') {
    await withLoading(async () => {
      await loadRiskTabData(symbol)
    })
    return
  }
  if (activeTab.value === 'fundamentals') {
    await withLoading(async () => {
      if (!fundamentals.value || fundamentals.value.symbol !== symbol) {
        fundamentals.value = await fetchInstrumentFundamentals(symbol)
      }
    })
    return
  }
  if (activeTab.value === 'etf') {
    await withLoading(async () => {
      if (!etfData.value || (etfData.value as EtfData & { symbol?: string }).symbol !== symbol) {
        etfData.value = await fetchInstrumentEtfData(symbol)
      }
    })
    return
  }
  if (activeTab.value === 'financials') {
    await withLoading(async () => {
      await loadFinancials(symbol)
    })
    return
  }
  await withLoading(async () => {
    await Promise.all([loadTimeseries(timeseriesSeries[0], false, symbol), loadRisk(symbol)])
  })
}

async function loadRiskTabData(symbol: string, force = false) {
  const shouldLoadCatalog = benchmarkCatalog.value.items.length === 0 || force
  const shouldLoadRisk = force || !risk.value || risk.value.symbol !== symbol || risk.value.benchmark !== benchmarkInput.value
  if (!shouldLoadCatalog && !shouldLoadRisk) return

  const [riskPayload, benchmarkPayload, catalogPayload] = await Promise.all([
    shouldLoadRisk ? fetchInstrumentRisk(symbol, benchmarkInput.value) : Promise.resolve(risk.value),
    shouldLoadRisk ? fetchInstrumentBenchmark(symbol, benchmarkInput.value) : Promise.resolve(null),
    shouldLoadCatalog ? fetchBenchmarkCatalog() : Promise.resolve(benchmarkCatalog.value)
  ])

  if (riskPayload) risk.value = riskPayload
  if (catalogPayload) benchmarkCatalog.value = catalogPayload
  if (benchmarkPayload?.benchmark && benchmarkPayload.benchmark !== benchmarkInput.value) {
    benchmarkAutoWarning.value = `Benchmark automatisch auf ${benchmarkPayload.benchmark} gesetzt.`
  } else {
    benchmarkAutoWarning.value = null
  }
  recomputeNonFinancialWarnings()
}

async function loadRisk(symbol: string, force = false) {
  const shouldLoad = force || !risk.value || risk.value.symbol !== symbol || risk.value.benchmark !== benchmarkInput.value
  if (!shouldLoad) return
  risk.value = await fetchInstrumentRisk(symbol, benchmarkInput.value)
  recomputeNonFinancialWarnings()
}

async function loadTimeseries(series: string, force = false, explicitSymbol?: string) {
  const symbol = explicitSymbol ?? props.selectedSymbol
  if (!symbol) return
  selectedSeries.value = series
  const shouldLoad =
    force ||
    !timeseries.value ||
    timeseries.value.symbol !== symbol ||
    timeseries.value.series !== series ||
    timeseries.value.benchmark_symbol !== benchmarkInput.value
  if (!shouldLoad) return
  timeseries.value = await fetchInstrumentTimeseries(symbol, series, benchmarkInput.value)
  recomputeNonFinancialWarnings()
}

async function reloadRisk() {
  if (!props.selectedSymbol) return
  await withLoading(async () => {
    await loadRiskTabData(props.selectedSymbol as string, true)
  })
}

function selectBenchmark(symbol: string) {
  benchmarkInput.value = symbol
  void applyBenchmark()
}

async function applyBenchmark() {
  if (!props.selectedSymbol) return
  if (activeTab.value === 'returns') {
    await withLoading(async () => {
      await loadTimeseries(selectedSeries.value, true)
    })
    return
  }
  if (activeTab.value === 'risk') {
    await withLoading(async () => {
      await loadRiskTabData(props.selectedSymbol as string, true)
    })
    return
  }
  if (activeTab.value === 'raw') {
    await withLoading(async () => {
      await Promise.all([loadTimeseries(timeseriesSeries[0], true), loadRisk(props.selectedSymbol as string, true)])
    })
  }
}

async function searchBenchmark() {
  const query = searchTerm.value.trim()
  if (!query) {
    benchmarkSearch.value = { query: '', items: [], total: 0 }
    return
  }
  benchmarkSearch.value = await searchBenchmarkCatalog(query)
}

async function loadFinancials(symbol = props.selectedSymbol ?? '') {
  if (!symbol) return
  if (financials.value?.symbol === symbol && financials.value.period === financialPeriod.value) return
  financials.value = await fetchInstrumentFinancials(symbol, financialPeriod.value)
  financialWarnings.value = (financials.value.meta?.warnings ?? [])
    .filter((w) => w.code !== 'etf_no_financial_statements')
    .map((entry) => `${entry.code}: ${entry.message}`)
}

function balanceSheetColumnTitle(row: DepotInstrumentBalanceSheetStatementRow) {
  return [row.date, row.period, row.fiscalYear != null ? `FY${row.fiscalYear}` : undefined].filter(Boolean).join(' · ') || 'Periode'
}

// ── Formatting helpers ──────────────────────────────────────────────────────

function fmtMoney(value: unknown, currency?: string | null): string {
  if (value == null || value === '') return '—'
  const num = typeof value === 'number' ? value : Number(value)
  if (!Number.isFinite(num)) return '—'
  const cur = currency ?? financialCurrency.value ?? undefined
  if (cur) {
    return new Intl.NumberFormat('de-DE', {
      style: 'currency',
      currency: cur,
      notation: 'compact',
      maximumFractionDigits: 2
    }).format(num)
  }
  return new Intl.NumberFormat('de-DE', { notation: 'compact', maximumFractionDigits: 2 }).format(num)
}

function fmtPercent(value: unknown): string {
  if (value == null) return '—'
  const num = typeof value === 'number' ? value : Number(value)
  if (!Number.isFinite(num)) return '—'
  return new Intl.NumberFormat('de-DE', {
    style: 'percent',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(num)
}

function fmtRatio(value: unknown): string {
  if (value == null) return '—'
  const num = typeof value === 'number' ? value : Number(value)
  if (!Number.isFinite(num)) return '—'
  return new Intl.NumberFormat('de-DE', { maximumFractionDigits: 2 }).format(num)
}

function fmtLarge(value: unknown): string {
  if (value == null) return '—'
  const num = typeof value === 'number' ? value : Number(value)
  if (!Number.isFinite(num)) return '—'
  return new Intl.NumberFormat('de-DE', { notation: 'compact', maximumFractionDigits: 2 }).format(num)
}

const SECTOR_NAMES: Record<string, string> = {
  technology: 'Technologie',
  financial_services: 'Finanzdienstleistungen',
  consumer_cyclical: 'Zyklischer Konsum',
  consumer_defensive: 'Nicht-zyklischer Konsum',
  healthcare: 'Gesundheit',
  industrials: 'Industrie',
  basic_materials: 'Rohstoffe',
  energy: 'Energie',
  utilities: 'Versorger',
  realestate: 'Immobilien',
  communication_services: 'Kommunikation'
}

function formatSectorName(key: string): string {
  return SECTOR_NAMES[key] ?? key
}

const ASSET_CLASS_NAMES: Record<string, string> = {
  stockPosition: 'Aktien',
  bondPosition: 'Anleihen',
  cashPosition: 'Cash',
  preferredPosition: 'Vorzugsaktien',
  convertiblePosition: 'Wandelanleihen',
  otherPosition: 'Sonstiges'
}

function formatAssetClassName(key: string): string {
  return ASSET_CLASS_NAMES[key] ?? key
}
</script>

<style scoped>
.tabs-root { display: grid; gap: 0.75rem; }
.tabs-head p { margin: 0.2rem 0 0; color: #64748b; }
.tabs-head h4 { display: flex; align-items: center; gap: 0.5rem; margin: 0; }
.type-badge {
  font-size: 0.7rem;
  font-weight: 600;
  padding: 0.15rem 0.45rem;
  border-radius: 999px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.badge-etf { background: #dbeafe; color: #1d4ed8; border: 1px solid #93c5fd; }
.badge-equity { background: #dcfce7; color: #15803d; border: 1px solid #86efac; }

.tab-nav { display: flex; flex-wrap: wrap; gap: 0.35rem; }
.tab-btn { border: 1px solid #cbd5e1; background: #f8fafc; border-radius: 8px; padding: 0.35rem 0.6rem; cursor: pointer; }
.tab-btn.active { background: #dbeafe; border-color: #60a5fa; color: #1d4ed8; }
.warning-box { border: 1px solid #f59e0b; background: #fffbeb; border-radius: 8px; padding: 0.45rem 0.65rem; color: #92400e; }
.content-card { padding: 0.8rem; }
.row-between { display: flex; justify-content: space-between; gap: 0.75rem; align-items: center; flex-wrap: wrap; }
.inline-row { display: flex; gap: 0.45rem; }
.input { border: 1px solid #cbd5e1; border-radius: 8px; padding: 0.35rem 0.55rem; }
.chip { border: 1px solid #cbd5e1; background: #f8fafc; border-radius: 999px; padding: 0.2rem 0.55rem; cursor: pointer; }
.chart-box { height: 260px; }

.kv-grid { display: grid; grid-template-columns: auto 1fr; gap: 0.35rem 0.7rem; margin: 0; }
.kv-grid dt { color: #475569; cursor: help; }
.kv-grid dd { margin: 0; color: #0f172a; }
.derived-grid { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 0.6rem; }

.blocks { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 0.55rem; }
.block { border: 1px solid #e2e8f0; border-radius: 8px; padding: 0.45rem; background: #f8fafc; }
.block h6 { margin: 0 0 0.25rem; }
.block p { margin: 0; }
.list { margin: 0.2rem 0 0; padding-left: 1.1rem; }
.link-btn { border: none; padding: 0; background: none; color: #2563eb; text-decoration: underline; cursor: pointer; }
.ext-link { color: #2563eb; word-break: break-all; }
.small { padding: 0.25rem 0.45rem; font-size: 0.8rem; cursor: pointer; }

/* Financials */
.financials-summary { margin: 0.35rem 0 0.65rem; color: #475569; font-size: 0.9rem; }
.period-chip-row { display: flex; flex-wrap: wrap; gap: 0.4rem; margin: 0.5rem 0 0.7rem; }
.period-chip {
  border: 1px solid #cbd5e1;
  background: #f8fafc;
  color: #334155;
  border-radius: 999px;
  padding: 0.28rem 0.62rem;
  font-size: 0.8rem;
  cursor: pointer;
}
.period-chip.active { background: #dbeafe; border-color: #60a5fa; color: #1e40af; }
.financials-detail-card {
  border: 1px solid #dbeafe;
  background: #f8fbff;
  border-radius: 10px;
  padding: 0.65rem;
  margin-bottom: 0.8rem;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 0.75rem;
}
.stmt-group-title { margin: 0 0 0.35rem; color: #1e40af; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em; }
.section-title { margin: 1rem 0 0.4rem; color: #334155; }
.history-compact { border: 1px solid #e2e8f0; border-radius: 10px; padding: 0.55rem; background: #ffffff; margin-bottom: 0.7rem; }
.history-compact h6 { margin: 0 0 0.45rem; }
.financials-compact-table { width: 100%; border-collapse: collapse; font-size: 0.84rem; table-layout: auto; }
.financials-compact-table th,
.financials-compact-table td {
  border-bottom: 1px solid #e2e8f0;
  text-align: left;
  padding: 0.38rem 0.45rem;
  white-space: nowrap;
}
.financials-compact-table th { color: #475569; font-weight: 600; cursor: help; }
.financials-compact-table tbody tr:last-child td { border-bottom: none; }

/* ETF */
.etf-notice {
  border: 1px solid #bfdbfe;
  background: #eff6ff;
  border-radius: 10px;
  padding: 0.75rem 1rem;
  color: #1e40af;
}
.etf-notice p { margin: 0 0 0.3rem; }
.etf-notice p:last-child { margin: 0; }
.fund-section { margin-bottom: 1.1rem; }
.fund-section h6 { margin: 0 0 0.45rem; color: #334155; cursor: help; }
.etf-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
.etf-table th, .etf-table td { border-bottom: 1px solid #e2e8f0; padding: 0.35rem 0.5rem; text-align: left; }
.etf-table th { color: #475569; font-weight: 600; }
.etf-table .mono { font-family: monospace; color: #0f172a; }
.etf-table .right { text-align: right; }

/* Bar chart for sector weights */
.bar-list { display: grid; gap: 0.4rem; }
.bar-row { display: grid; grid-template-columns: 140px 1fr 60px; gap: 0.4rem; align-items: center; font-size: 0.82rem; }
.bar-label { color: #334155; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.bar-track { background: #e2e8f0; border-radius: 999px; height: 8px; overflow: hidden; }
.bar-fill { background: #3b82f6; height: 100%; border-radius: 999px; transition: width 0.3s ease; }
.bar-value { color: #475569; text-align: right; }
.description-text { margin: 0.6rem 0 0; font-size: 0.85rem; color: #475569; line-height: 1.5; }
</style>
