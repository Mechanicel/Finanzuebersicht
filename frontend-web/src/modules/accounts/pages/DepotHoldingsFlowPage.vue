<template>
  <section class="card">
    <div class="view-header">
      <div class="view-header-copy">
        <p class="eyebrow">Depot-Flow · separater Schritt</p>
        <h2>Depotpositionen verwalten</h2>
        <p v-if="personId && depotLabel">Depot: {{ depotLabel }}</p>
      </div>
      <RouterLink class="btn flow-btn" :to="backTarget">{{ backLabel }}</RouterLink>
    </div>

    <p v-if="!personId || !depotLabel" class="context-hint">
      Kein vollständiger Kontext für die Depotverwaltung vorhanden. Bitte starte den Flow über „Konto hinzufügen“
      oder „Konten ansehen & bearbeiten“.
    </p>

    <template v-else>
      <p class="muted">Dieser Schritt ist bewusst getrennt vom Kontoformular, um die Depotpflege übersichtlich zu halten.</p>
      <DepotHoldingsManager :person-id="personId" :depot-label="depotLabel" title="Depot-Positionen" />
      <div class="actions">
        <RouterLink class="btn" :to="backTarget">Depot-Flow abschließen</RouterLink>
      </div>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import DepotHoldingsManager from '@/modules/accounts/components/DepotHoldingsManager.vue'

const route = useRoute()

const personId = computed(() => (typeof route.query.personId === 'string' ? route.query.personId : ''))
const depotLabel = computed(() => (typeof route.query.depotLabel === 'string' ? route.query.depotLabel : ''))
const origin = computed(() => (typeof route.query.origin === 'string' ? route.query.origin : 'create'))

const backTarget = computed(() => {
  if (!personId.value) {
    return '/persons/select'
  }
  if (origin.value === 'manage') {
    return `/accounts/manage?personId=${personId.value}`
  }
  return `/persons/${personId.value}`
})

const backLabel = computed(() => (origin.value === 'manage' ? 'Zurück zu Konten bearbeiten' : 'Zurück zum Personen-Hub'))
</script>

<style scoped>
.eyebrow {
  margin: 0;
  color: #475569;
  font-weight: 600;
}

.context-hint {
  margin-top: 0;
  color: #92400e;
  background: #fffbeb;
  border: 1px solid #fcd34d;
  border-radius: 8px;
  padding: 0.65rem 0.75rem;
}

.actions {
  margin-top: 1rem;
}
</style>
