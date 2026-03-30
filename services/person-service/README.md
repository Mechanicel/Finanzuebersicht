# person-service

Eigenständiger FastAPI-Service für Personen, Person↔Bank-Zuordnungen und Freibeträge.

## Architektur

Der Service modelliert die Domäne **entkoppelt** in drei Ressourcen:

- `Person`
- `PersonBankAssignment`
- `TaxAllowance`

Es gibt **keine** eingebetteten Legacy-Gesamtdokumente und **keine** implizite Kopplung zum `account-service`.

## Persistenz (MongoDB)

Der Service verwendet standardmäßig MongoDB (kein In-Memory-CRUD-Default mehr).

### Settings

- `MONGO_URI` (optional, direkte URI)
- Fallback bei leerem `MONGO_URI`:
  - `MONGO_HOST` (default `localhost`)
  - `MONGO_PORT` (default `27017`)
  - `MONGO_DATABASE` (default `finanzuebersicht`)
  - `MONGO_USER` (optional)
  - `MONGO_PASSWORD` (optional)
  - `MONGO_AUTH_SOURCE` (default `admin`)

Wenn `MONGO_USER`/`MONGO_PASSWORD` leer sind, wird ohne Authentifizierung verbunden.

### Collections

- `MONGO_PERSON_COLLECTION` (default `persons`)
- `MONGO_ASSIGNMENT_COLLECTION` (default `person_bank_assignments`)
- `MONGO_ALLOWANCE_COLLECTION` (default `tax_allowances`)

MongoDB legt Collections automatisch beim ersten Schreiben an. Benötigte Indizes werden beim Initialisieren des Repositories erstellt.

## API (v1)

Basis-Prefix: `/api/v1`

### Personen

- `GET /persons` (Suche/Sortierung/Pagination)
- `POST /persons`
- `GET /persons/{person_id}`
- `PATCH /persons/{person_id}`
- `DELETE /persons/{person_id}`

### Person-Bank-Zuordnungen

- `GET /persons/{person_id}/banks`
- `POST /persons/{person_id}/banks/{bank_id}`
- `DELETE /persons/{person_id}/banks/{bank_id}`

### Freibeträge

- `GET /persons/{person_id}/allowances`
- `PUT /persons/{person_id}/allowances/{bank_id}?amount=801.25`
- `GET /persons/{person_id}/allowances/summary`

## Frontend-Flow

Personen-CRUD läuft lokal über:

`frontend-web -> api-gateway -> person-service -> MongoDB`

## Entwicklung

```bash
uv sync --all-packages --dev
PYTHONPATH=services/person-service:shared/src uv run --all-packages pytest services/person-service/tests/test_person_api.py
```
