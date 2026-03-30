<template>
  <section class="card quickstart">
    <h2>Schnellstart</h2>
    <p class="subtitle">
      Wähle den passenden Einstieg: bestehende Person öffnen, eine neue Person erfassen oder eine neue Bank anlegen.
    </p>

    <div class="quickstart-actions">
      <RouterLink class="action-card" to="/persons/select">
        <h3>Person auswählen</h3>
        <p>Zur Personensuche wechseln und mit einer bestehenden Person weiterarbeiten.</p>
      </RouterLink>

      <RouterLink class="action-card" to="/persons/new">
        <h3>Neue Person anlegen</h3>
        <p>Direkt in den Erfassungsscreen wechseln und eine neue Person anlegen.</p>
      </RouterLink>

      <RouterLink class="action-card" to="/banks/new">
        <h3>Neue Bank anlegen</h3>
        <p>Zum Bank-Startscreen wechseln und eine neue Bankverbindung vorbereiten.</p>
      </RouterLink>
    </div>
  </section>
</template>

<style scoped>
.quickstart {
  padding: 1.5rem;
}

.subtitle {
  color: #475569;
  margin-top: 0.35rem;
  margin-bottom: 1.5rem;
}

.quickstart-actions {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1rem;
}

.action-card {
  display: block;
  padding: 1rem;
  border: 1px solid #cbd5e1;
  border-radius: 12px;
  text-decoration: none;
  color: #0f172a;
  background: #f8fafc;
  min-height: 180px;
}

.action-card:hover {
  border-color: #2563eb;
  background: #eff6ff;
}

.action-card h3 {
  margin-top: 0;
  margin-bottom: 0.7rem;
}

.action-card p {
  margin: 0;
  color: #475569;
}
</style>
