<template><p class="error">Fehler: {{ message }}</p></template>
<script setup lang="ts">
defineProps<{ message: string }>()
</script>
