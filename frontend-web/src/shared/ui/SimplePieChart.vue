<template><Pie :data="chartData" :options="options" /></template>
<script setup lang="ts">
import { computed } from 'vue'
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js'
import { Pie } from 'vue-chartjs'
ChartJS.register(ArcElement, Tooltip, Legend)
const props = defineProps<{ labels: string[]; values: number[] }>()
const chartData = computed(() => ({
  labels: props.labels,
  datasets: [{ data: props.values, backgroundColor: ['#2563eb', '#16a34a', '#f59e0b', '#9333ea', '#ef4444'] }]
}))
const options = { responsive: true, maintainAspectRatio: false }
</script>
