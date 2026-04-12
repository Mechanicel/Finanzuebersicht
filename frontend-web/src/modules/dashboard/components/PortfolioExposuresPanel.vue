<template>
  <article class="panel">
    <h3>Exposures / Allocation</h3>

    <section v-for="section in sections" :key="section.key" class="exposure-section">
      <header class="section-header">
        <h4>{{ section.title }}</h4>
        <button v-if="section.items.length > 8" type="button" class="toggle" @click="toggleSection(section.key)">
          {{ expandedSections[section.key] ? 'Weniger anzeigen' : 'Mehr anzeigen' }}
        </button>
      </header>
      <ul v-if="section.items.length > 0">
        <li v-for="item in visibleItems(section)" :key="`${section.key}-${item.label}`">
          <span>{{ item.label }}</span>
          <span class="market-value">{{ formatMoney(item.market_value, currency) }}</span>
          <strong class="weight">{{ formatPercent(item.weight) }}</strong>
        </li>
      </ul>
      <p v-else class="hint">Keine Daten</p>
    </section>
  </article>
</template>

<script setup lang="ts">
import { computed, reactive } from 'vue'
import type { PortfolioExposuresReadModel } from '@/shared/model/types'
import { formatMoney, formatPercent } from '@/modules/dashboard/model/portfolioFormatting'

const props = defineProps<{
  exposures: PortfolioExposuresReadModel
  currency?: string
}>()

const currency = computed(() => props.currency ?? 'EUR')

function sortByWeight<T extends { weight: number; market_value: number }>(items: T[]) {
  return [...items].sort((left, right) => right.weight - left.weight || right.market_value - left.market_value)
}

const sections = computed(() => [
  { key: 'position', title: 'Positionen', items: sortByWeight(props.exposures.by_position) },
  { key: 'sector', title: 'Sektoren', items: sortByWeight(props.exposures.by_sector) },
  { key: 'country', title: 'Länder', items: sortByWeight(props.exposures.by_country) },
  { key: 'currency', title: 'Währungen', items: sortByWeight(props.exposures.by_currency) }
])

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

.exposure-section + .exposure-section {
  margin-top: 0.56rem;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

h4 {
  margin: 0 0 0.28rem;
  font-size: 0.9rem;
  color: #334155;
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
  margin: 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 0.25rem;
}

li {
  display: grid;
  grid-template-columns: 1fr auto auto;
  gap: 0.45rem;
  font-size: 0.82rem;
  align-items: baseline;
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
</style>
