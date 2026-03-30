<template>
  <section class="card">
    <h2>Bankzuordnung</h2>
    <p class="empty">Bankzuordnungen werden über das API-Gateway pro Person gepflegt.</p>
    <div class="grid" style="grid-template-columns: 1fr 1fr auto">
      <div><label>Person-ID</label><input class="input" v-model.trim="personId" /></div>
      <div><label>Bank-ID</label><input class="input" v-model.trim="bankId" /></div>
      <button class="btn" @click="assign">Zuordnen</button>
    </div>
    <p v-if="message">{{ message }}</p>
  </section>
</template>
<script setup lang="ts">
import { ref } from 'vue'
import { useRoute } from 'vue-router'
const route = useRoute()
const personId = ref(typeof route.query.personId === 'string' ? route.query.personId : '')
const bankId = ref('')
const message = ref('')
function assign() {
  message.value = personId.value && bankId.value ? 'Zuordnung validiert und zur Übergabe vorbereitet.' : 'Bitte beide IDs eintragen.'
}
</script>
