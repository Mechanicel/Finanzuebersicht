<template>
  <section class="card">
    <h2>Freibetragsverwaltung</h2>
    <div class="grid" style="grid-template-columns: 1fr 1fr 1fr auto">
      <div><label>Person-ID</label><input class="input" v-model.trim="personId" /></div>
      <div><label>Bank-ID</label><input class="input" v-model.trim="bankId" /></div>
      <div><label>Betrag (EUR)</label><input class="input" type="number" min="0" step="0.01" v-model.number="amount" /></div>
      <button class="btn" @click="save">Speichern</button>
    </div>
    <p v-if="error" class="error">{{ error }}</p>
    <p v-if="ok">Freibetrag-Änderung validiert und bereit für Gateway-Submit.</p>
  </section>
</template>
<script setup lang="ts">
import { ref } from 'vue'
import { useRoute } from 'vue-router'
const route = useRoute()
const personId = ref(typeof route.query.personId === 'string' ? route.query.personId : '')
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
