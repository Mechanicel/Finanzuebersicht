<template>
  <section class="card">
    <div class="view-header">
      <div class="view-header-copy">
        <h2>Freibetragsverwaltung</h2>
        <p>Pflege Freibeträge im Kontext einer ausgewählten Person.</p>
      </div>
      <RouterLink class="btn flow-btn" :to="backTarget">{{ backLabel }}</RouterLink>
    </div>
    <p v-if="!hasPersonContext" class="context-hint">
      Bitte zuerst eine Person auswählen und Freibeträge aus dem Personen-Hub öffnen.
    </p>
    <div class="grid" style="grid-template-columns: 1fr 1fr 1fr auto">
      <div><label>Person-ID</label><input class="input" v-model.trim="personId" /></div>
      <div><label>Bank-ID</label><input class="input" v-model.trim="bankId" /></div>
      <div><label>Betrag (EUR)</label><input class="input" type="number" min="0" step="0.01" v-model.number="amount" /></div>
      <button class="btn" @click="save" :disabled="!hasPersonContext">Speichern</button>
    </div>
    <p v-if="error" class="error">{{ error }}</p>
    <p v-if="ok">Freibetrag-Änderung validiert und bereit für Gateway-Submit.</p>
  </section>
</template>
<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
const route = useRoute()
const personId = ref(typeof route.query.personId === 'string' ? route.query.personId : '')
const hasPersonContext = typeof route.query.personId === 'string' && route.query.personId.length > 0
const backTarget = computed(() =>
  hasPersonContext ? `/persons/${route.query.personId as string}` : '/persons/select'
)
const backLabel = computed(() => (hasPersonContext ? 'Zurück zum Personen-Hub' : 'Zur Personenliste'))
const bankId = ref('')
const amount = ref<number | null>(null)
const error = ref('')
const ok = ref(false)
function save() {
  ok.value = false
  error.value = ''
  if (!personId.value || !bankId.value || amount.value === null || amount.value < 0) {
    error.value = 'Alle Felder sind erforderlich, Betrag >= 0.'
    return
  }
  ok.value = true
}
</script>

<style scoped>
.context-hint {
  margin-top: 0;
  margin-bottom: 0.75rem;
  color: #92400e;
  background: #fffbeb;
  border: 1px solid #fcd34d;
  border-radius: 8px;
  padding: 0.65rem 0.75rem;
}

</style>
