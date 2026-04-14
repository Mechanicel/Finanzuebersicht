<template><Line :data="chartData" :options="options" /></template>
<script setup lang="ts">
import { computed } from 'vue'
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend } from 'chart.js'
import { Line } from 'vue-chartjs'
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend)

type LinePoint = { date: string; value: number }
type LineDataset = { label: string; points: LinePoint[]; borderColor?: string }

const props = defineProps<{ points: LinePoint[]; datasets?: LineDataset[] }>()

const chartData = computed(() => ({
  labels: (props.datasets?.[0]?.points ?? props.points).map((x) => x.date),
  datasets:
    props.datasets && props.datasets.length > 0
      ? props.datasets.map((dataset, index) => ({
          label: dataset.label,
          data: dataset.points.map((x) => x.value),
          borderColor: dataset.borderColor ?? (index === 0 ? '#2563eb' : '#0e7490'),
          tension: 0.25
        }))
      : [{ label: 'Vermögen', data: props.points.map((x) => x.value), borderColor: '#2563eb', tension: 0.25 }]
}))
const options = { responsive: true, maintainAspectRatio: false }
</script>
