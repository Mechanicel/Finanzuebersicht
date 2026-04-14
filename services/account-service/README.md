# account-service

FastAPI-Service-Skeleton im Finanzuebersicht-Monorepo.

## Persistenz

- Standardmäßig nutzt der Service das persistente MongoDB-Repository (`ACCOUNT_REPOSITORY_BACKEND=mongo`).
- `InMemoryAccountRepository` bleibt für Tests und als Fallback via `ACCOUNT_REPOSITORY_BACKEND=inmemory` verfügbar.

### Relevante Environment-Variablen

- `ACCOUNT_REPOSITORY_BACKEND` (`mongo` oder `inmemory`, Default: `mongo`)
- `MONGO_URI` (optional, überschreibt Host/Port/User/Pass-Aufbau vollständig)
- `MONGO_HOST` (Default: `localhost`)
- `MONGO_PORT` (Default: `27017`)
- `MONGO_DATABASE` (Default: `finanzuebersicht`)
- `MONGO_USER` / `MONGO_PASSWORD` (optional)
- `MONGO_AUTH_SOURCE` (Default: `admin`)
- `MONGO_ACCOUNTS_COLLECTION` (Default: `accounts`)
