<template>
  <article class="panel">
    <h3>Exposures / Allocation</h3>

    <section v-for="section in sections" :key="section.key" class="exposure-section">
      <h4>{{ section.title }}</h4>
      <ul v-if="section.items.length > 0">
        <li v-for="item in section.items" :key="`${section.key}-${item.label}`">
          <span>{{ item.label }}</span>
          <span>{{ formatMoney(item.market_value, currency) }}</span>
          <strong>{{ formatPercent(item.weight) }}</strong>
        </li>
      </ul>
      <p v-else class="hint">Keine Daten</p>
    </section>
  </article>
</template>

<script setup lang="ts">
import { computed } from 'vue'
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
  margin-top: 0.7rem;
}

h4 {
  margin: 0 0 0.35rem;
  font-size: 0.9rem;
  color: #334155;
}

ul {
  margin: 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 0.35rem;
}

li {
  display: grid;
  grid-template-columns: 1fr auto auto;
  gap: 0.6rem;
  font-size: 0.86rem;
}

.hint {
  margin: 0;
  font-size: 0.85rem;
  color: #64748b;
}
</style>
