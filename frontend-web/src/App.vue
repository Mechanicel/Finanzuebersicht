<template>
  <div class="container">
    <h1>Finanzübersicht</h1>
    <nav class="nav">
      <RouterLink to="/">Start</RouterLink>
      <RouterLink to="/dashboard">Dashboard</RouterLink>
      <RouterLink to="/persons">Personen</RouterLink>
      <RouterLink to="/banks/new">Neue Bank</RouterLink>
      <RouterLink to="/bank-assignments">Bankzuordnung</RouterLink>
      <RouterLink to="/allowances">Freibeträge</RouterLink>
      <RouterLink to="/accounts">Konten</RouterLink>
      <RouterLink to="/holdings">Depot/Holdings</RouterLink>
    </nav>
    <RouterView />
  </div>
</template>
