<template>
  <section class="portfolio-value-chart" aria-live="polite">
    <div class="portfolio-value-chart__header">
      <slot name="title">
        <h3 class="portfolio-value-chart__title">Portfolioentwicklung</h3>
      </slot>
      <div class="portfolio-value-chart__ranges" role="group" aria-label="Zeitraum wählen">
        <button
          v-for="option in rangeOptions"
          :key="option.value"
          type="button"
          class="range-button"
          :class="{ 'range-button--active': option.value === range }"
          :aria-pressed="option.value === range"
          @click="onRangeSelect(option.value)"
        >
          {{ option.label }}
        </button>
      </div>
    </div>

    <div v-if="loading" class="portfolio-value-chart__state">Lade Kursverlauf …</div>
    <div v-else-if="error" class="portfolio-value-chart__state portfolio-value-chart__state--error">{{ error }}</div>
    <div v-else-if="!points.length" class="portfolio-value-chart__state">Keine Verlaufspunkte vorhanden.</div>

    <div v-else class="portfolio-value-chart__canvas-wrap">
      <Line :data="chartData" :options="chartOptions" />
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Line } from 'vue-chartjs'
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend, type TooltipItem } from 'chart.js'
import type { InstrumentHistoryRange } from '@/shared/model/types'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend)

interface PortfolioValuePoint {
  date: string
  value: number
}

const props = withDefaults(
  defineProps<{
    points: PortfolioValuePoint[]
    range: InstrumentHistoryRange
    loading?: boolean
    error?: string
  }>(),
  {
    loading: false,
    error: ''
  }
)

const emit = defineEmits<{
  'range-change': [range: InstrumentHistoryRange]
}>()

const rangeOptions: Array<{ label: string; value: InstrumentHistoryRange }> = [
  { label: '1M', value: '1m' },
  { label: '3M', value: '3m' },
  { label: '6M', value: '6m' },
  { label: 'YTD', value: 'ytd' },
  { label: '1Y', value: '1y' },
  { label: 'MAX', value: 'max' }
]

const dateFormatter = new Intl.DateTimeFormat('de-DE', {
  day: '2-digit',
  month: '2-digit',
  year: 'numeric'
})

const currencyFormatter = new Intl.NumberFormat('de-DE', {
  style: 'currency',
  currency: 'EUR'
})

const chartData = computed(() => ({
  labels: props.points.map((point) => dateFormatter.format(new Date(point.date))),
  datasets: [
    {
      label: 'Portfoliowert',
      data: props.points.map((point) => point.value),
      borderColor: '#2563eb',
      backgroundColor: 'rgba(37, 99, 235, 0.2)',
      pointRadius: 2,
      pointHoverRadius: 5,
      tension: 0.2,
      fill: true
    }
  ]
}))

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: {
    mode: 'index' as const,
    intersect: false
  },
  plugins: {
    legend: { display: false },
    tooltip: {
      callbacks: {
        label(context: TooltipItem<'line'>) {
          const value = Number(context.raw ?? 0)
          return currencyFormatter.format(value)
        }
      }
    }
  },
  scales: {
    x: {
      ticks: { maxTicksLimit: 6 }
    },
    y: {
      ticks: {
        callback(value: string | number) {
          return currencyFormatter.format(Number(value))
        }
      }
    }
  }
}

function onRangeSelect(range: InstrumentHistoryRange) {
  emit('range-change', range)
}
</script>

<style scoped>
.portfolio-value-chart {
  display: grid;
  gap: 0.75rem;
}

.portfolio-value-chart__header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.portfolio-value-chart__title {
  margin: 0;
  font-size: 1rem;
}

.portfolio-value-chart__ranges {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}

.range-button {
  border: 1px solid #d1d5db;
  background: #fff;
  color: #111827;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.25rem 0.6rem;
  cursor: pointer;
}

.range-button--active {
  background: #2563eb;
  border-color: #2563eb;
  color: #fff;
}

.portfolio-value-chart__canvas-wrap {
  height: 280px;
}

.portfolio-value-chart__state {
  border: 1px dashed #d1d5db;
  border-radius: 0.5rem;
  padding: 1rem;
  color: #4b5563;
  font-size: 0.9rem;
}

.portfolio-value-chart__state--error {
  color: #b91c1c;
  border-color: #fecaca;
  background: #fef2f2;
}
</style>
