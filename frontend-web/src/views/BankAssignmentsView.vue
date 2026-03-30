<template>
  <section class="card">
    <h2>Bankzuordnung</h2>
    <p v-if="!hasPersonContext" class="context-hint">
      Bitte zuerst eine Person auswählen und Bankzuordnungen aus dem Personen-Hub öffnen.
      <RouterLink to="/persons">Zur Personenliste</RouterLink>
    </p>
    <p class="empty">Bankzuordnungen werden über das API-Gateway pro Person gepflegt.</p>
    <div class="grid" style="grid-template-columns: 1fr 1fr auto">
      <div><label>Person-ID</label><input class="input" v-model.trim="personId" /></div>
      <div><label>Bank-ID</label><input class="input" v-model.trim="bankId" /></div>
      <button class="btn" @click="assign" :disabled="!hasPersonContext">Zuordnen</button>
    </div>
    <p v-if="message">{{ message }}</p>
  </section>
</template>
<script setup lang="ts">
import { ref } from 'vue'
import { useRoute } from 'vue-router'
const route = useRoute()
const personId = ref(typeof route.query.personId === 'string' ? route.query.personId : '')
const hasPersonContext = typeof route.query.personId === 'string' && route.query.personId.length > 0
const bankId = ref('')
const message = ref('')
function assign() {
  message.value = personId.value && bankId.value ? 'Zuordnung validiert und zur Übergabe vorbereitet.' : 'Bitte beide IDs eintragen.'
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

.context-hint :deep(a) {
  margin-left: 0.35rem;
}
</style>
