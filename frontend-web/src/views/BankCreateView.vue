<template>
  <section class="card">
    <div class="header-row">
      <h2>Neue Bank anlegen</h2>
      <RouterLink class="btn flow-btn" to="/">Zur Startseite</RouterLink>
    </div>
    <p class="empty">
      Hier startest du den Bankfluss. Erfasse eine Bank-ID und einen Namen, um die Anlage vorzubereiten.
    </p>

    <div class="grid" style="grid-template-columns: 1fr 1fr auto; align-items: end; margin-top: 1rem">
      <div><label>Bank-ID</label><input class="input" v-model.trim="bankId" /></div>
      <div><label>Bankname</label><input class="input" v-model.trim="bankName" /></div>
      <button class="btn" @click="prepareBank">Bank vorbereiten</button>
    </div>

    <p v-if="message" style="margin-top: 1rem">{{ message }}</p>
  </section>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const bankId = ref('')
const bankName = ref('')
const message = ref('')

function prepareBank() {
  message.value = bankId.value && bankName.value
    ? `Bank ${bankName.value} (${bankId.value}) ist für den nächsten Schritt erfasst.`
    : 'Bitte Bank-ID und Bankname ausfüllen.'
}
</script>

<style scoped>
.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.75rem;
}
</style>
