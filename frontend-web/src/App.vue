<template>
  <div class="container">
    <h1>Finanzübersicht</h1>
    <nav class="nav">
      <RouterLink to="/">Start</RouterLink>
      <RouterLink to="/persons">Personen</RouterLink>
      <RouterLink to="/banks/new">Neue Bank</RouterLink>
    </nav>
    <RouterView />
  </div>
</template>
