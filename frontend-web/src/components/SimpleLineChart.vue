<template><Line :data="chartData" :options="options" /></template>
<script setup lang="ts">
import { computed } from 'vue'
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend } from 'chart.js'
import { Line } from 'vue-chartjs'
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend)
const props = defineProps<{ points: { date: string; value: number }[] }>()
const chartData = computed(() => ({
  labels: props.points.map((x) => x.date),
  datasets: [{ label: 'Vermögen', data: props.points.map((x) => x.value), borderColor: '#2563eb', tension: 0.25 }]
}))
const options = { responsive: true, maintainAspectRatio: false }
</script>
