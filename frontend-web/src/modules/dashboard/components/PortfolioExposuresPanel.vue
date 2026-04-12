<template>
  <article class="panel" data-testid="portfolio-exposures-panel" :data-layout="presentationState">
    <h3>Exposures / Allocation</h3>

    <div
      v-if="usesCompactLayout"
      class="compact-sections-layout"
      :data-testid="presentationState === 'empty' ? 'exposures-empty-state' : 'exposures-small-state'"
    >
      <section
        v-for="section in sections"
        :key="section.key"
        class="exposure-section exposure-section--balanced"
        :data-testid="`exposure-card-${section.key}`"
      >
        <header class="section-header">
          <h4>{{ section.title }}</h4>
          <span class="section-count">{{ section.items.length }}</span>
        </header>
        <ul v-if="section.items.length > 0" class="compact-exposure-list">
          <li
            v-for="item in section.items"
            :key="`${section.key}-${item.label}`"
            class="compact-exposure-item"
            :data-testid="`exposure-small-row-${section.key}`"
          >
            <div class="compact-exposure-main">
              <span class="exposure-label">{{ item.label }}</span>
              <strong class="weight">{{ formatPercent(item.weight) }}</strong>
            </div>
            <div class="exposure-bar" aria-hidden="true">
              <span :style="{ width: exposureBarWidth(item.weight) }"></span>
            </div>
            <span class="market-value">{{ formatMoney(item.market_value, currency) }}</span>
          </li>
        </ul>
        <p v-else class="hint" :data-testid="`exposure-empty-${section.key}`">Keine Daten</p>
      </section>
    </div>

    <div v-else class="sections-layout" data-testid="exposures-default-state">
      <section class="exposure-section exposure-section--primary">
        <header class="section-header">
          <h4>{{ positionSection.title }}</h4>
          <button
            v-if="positionSection.items.length > 8"
            type="button"
            class="toggle"
            @click="toggleSection(positionSection.key)"
          >
            {{ expandedSections[positionSection.key] ? 'Weniger anzeigen' : 'Mehr anzeigen' }}
          </button>
        </header>
        <ul v-if="positionSection.items.length > 0">
          <li
            v-for="item in visibleItems(positionSection)"
            :key="`${positionSection.key}-${item.label}`"
            :data-testid="`exposure-default-row-${positionSection.key}`"
          >
            <span>{{ item.label }}</span>
            <span class="market-value">{{ formatMoney(item.market_value, currency) }}</span>
            <strong class="weight">{{ formatPercent(item.weight) }}</strong>
          </li>
        </ul>
        <p v-else class="hint" :data-testid="`exposure-empty-${positionSection.key}`">Keine Daten</p>
      </section>

      <div class="sections-sidebar">
        <section
          v-for="section in secondarySections"
          :key="section.key"
          class="exposure-section exposure-section--compact"
          :data-testid="`exposure-default-section-${section.key}`"
        >
          <header class="section-header">
            <h4>{{ section.title }}</h4>
            <button v-if="section.items.length > 8" type="button" class="toggle" @click="toggleSection(section.key)">
              {{ expandedSections[section.key] ? 'Weniger anzeigen' : 'Mehr anzeigen' }}
            </button>
          </header>
          <ul v-if="section.items.length > 0">
            <li
              v-for="item in visibleItems(section)"
              :key="`${section.key}-${item.label}`"
              :data-testid="`exposure-default-row-${section.key}`"
            >
              <span>{{ item.label }}</span>
              <span class="market-value">{{ formatMoney(item.market_value, currency) }}</span>
              <strong class="weight">{{ formatPercent(item.weight) }}</strong>
            </li>
          </ul>
          <p v-else class="hint" :data-testid="`exposure-empty-${section.key}`">Keine Daten</p>
        </section>
      </div>
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed, reactive } from 'vue'
import type { PortfolioExposureSlice, PortfolioExposuresReadModel } from '@/shared/model/types'
import { formatMoney, formatPercent } from '@/modules/dashboard/model/portfolioFormatting'

const props = defineProps<{
  exposures: PortfolioExposuresReadModel
  currency?: string
}>()

const SMALL_PORTFOLIO_POSITION_LIMIT = 3

type ExposureSectionKey = 'position' | 'sector' | 'country' | 'currency'

interface ExposureSection {
  key: ExposureSectionKey
  title: string
  items: PortfolioExposureSlice[]
}

const currency = computed(() => props.currency ?? 'EUR')

function sortByWeight<T extends { weight: number; market_value: number }>(items: T[]) {
  return [...items].sort((left, right) => right.weight - left.weight || right.market_value - left.market_value)
}

const sections = computed<ExposureSection[]>(() => [
  { key: 'position', title: 'Positionen', items: sortByWeight(props.exposures.by_position) },
  { key: 'sector', title: 'Sektoren', items: sortByWeight(props.exposures.by_sector) },
  { key: 'country', title: 'L\u00e4nder', items: sortByWeight(props.exposures.by_country) },
  { key: 'currency', title: 'W\u00e4hrungen', items: sortByWeight(props.exposures.by_currency) }
])

const positionSection = computed(() => sections.value[0])
const secondarySections = computed(() => sections.value.slice(1))
const hasExposureData = computed(() => sections.value.some((section) => section.items.length > 0))
const isSmallPortfolio = computed(
  () => positionSection.value.items.length > 0 && positionSection.value.items.length <= SMALL_PORTFOLIO_POSITION_LIMIT
)
const usesCompactLayout = computed(() => isSmallPortfolio.value || !hasExposureData.value)
const presentationState = computed(() => (isSmallPortfolio.value ? 'small' : hasExposureData.value ? 'default' : 'empty'))

const expandedSections = reactive<Record<string, boolean>>({
  position: false,
  sector: false,
  country: false,
  currency: false
})

function visibleItems<T extends { label: string; weight: number; market_value: number }>(section: { key: string; items: T[] }) {
  return expandedSections[section.key] ? section.items : section.items.slice(0, 8)
}

function toggleSection(key: string) {
  expandedSections[key] = !expandedSections[key]
}

function exposureBarWidth(weight: number) {
  if (!Number.isFinite(weight)) {
    return '0%'
  }

  return `${Math.min(100, Math.max(0, weight * 100))}%`
}
</script>

<style scoped>
.panel {
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 0.9rem;
  background: #fff;
}

h3 {
  margin: 0 0 0.5rem;
}

.compact-sections-layout {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.5rem;
  align-items: start;
}

.sections-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.5fr) minmax(0, 1fr);
  gap: 0.6rem;
  align-items: start;
}

.sections-sidebar {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.6rem;
  align-items: start;
}

.exposure-section {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 0.45rem 0.5rem;
}

.exposure-section--compact {
  padding: 0.35rem 0.42rem;
}

.exposure-section--balanced {
  min-width: 0;
  padding: 0.45rem 0.5rem;
  background: #f8fafc;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

h4 {
  margin: 0;
  font-size: 0.9rem;
  color: #334155;
}

.section-count {
  min-width: 1.35rem;
  border: 1px solid #cbd5e1;
  border-radius: 999px;
  padding: 0.05rem 0.32rem;
  color: #475569;
  font-size: 0.7rem;
  font-weight: 700;
  line-height: 1.35;
  text-align: center;
}

.toggle {
  border: 1px solid #cbd5e1;
  border-radius: 999px;
  background: #fff;
  color: #475569;
  font-size: 0.72rem;
  line-height: 1;
  padding: 0.2rem 0.45rem;
  cursor: pointer;
}

ul {
  margin: 0.2rem 0 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 0.18rem;
}

li {
  display: grid;
  grid-template-columns: 1fr auto auto;
  gap: 0.45rem;
  font-size: 0.78rem;
  align-items: baseline;
}

.compact-exposure-list {
  gap: 0.38rem;
}

.compact-exposure-item {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.18rem;
  align-items: stretch;
  font-size: 0.78rem;
}

.compact-exposure-main {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 0.45rem;
  min-width: 0;
}

.exposure-label {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.exposure-bar {
  width: 100%;
  height: 0.38rem;
  overflow: hidden;
  border-radius: 999px;
  background: #e2e8f0;
}

.exposure-bar span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: #0f766e;
}

.compact-exposure-item .market-value {
  font-size: 0.72rem;
  line-height: 1.2;
}

.market-value {
  color: #475569;
}

.weight {
  font-weight: 700;
}

.hint {
  margin: 0;
  font-size: 0.85rem;
  color: #64748b;
}

@media (max-width: 1100px) {
  .compact-sections-layout {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .sections-layout {
    grid-template-columns: 1fr;
  }

  .sections-sidebar {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 700px) {
  .compact-sections-layout,
  .sections-layout {
    grid-template-columns: 1fr;
  }
}
</style>
