# person-service

Eigenständiger FastAPI-Service für Personen, Person↔Bank-Zuordnungen und Freibeträge.

## Architektur

Der Service modelliert die Domäne **entkoppelt** in drei Ressourcen:

- `Person`
- `PersonBankAssignment`
- `TaxAllowance`

Es gibt **keine** eingebetteten Legacy-Gesamtdokumente und **keine** implizite Kopplung zum `account-service`.

Zusätzlich hat `Person` ein `tax_profile` (`tax_country`, `filing_status`) mit Default `DE/single`.
Die aktuelle Übergangsannahme lautet: `filing_status=joint` ist vorerst eine Eigenschaft einer einzelnen Person.
Eine spätere echte steuerliche Einheit (`tax unit`) würde als eigene Entität oberhalb von Personen ansetzen, und die
Allowance-Policy würde dann auf dieser Einheit statt auf einer einzelnen Person ausgewertet.

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

- `GET /persons/{person_id}/allowances?tax_year=2026` (`tax_year` optional)
- `PUT /persons/{person_id}/allowances/{bank_id}` mit Body `{ "tax_year": 2026, "amount": "801.25", "currency": "EUR" }`
- `GET /persons/{person_id}/allowances/summary?tax_year=2026`

Allowances sind fachlich pro `(person_id, bank_id, tax_year)` eindeutig. Der Mongo-Unique-Index folgt diesem Schlüssel.
Pragmatische Behandlung von Alt-Dokumenten ohne `tax_year`: sie werden beim Lesen als aktuelles UTC-Steuerjahr
interpretiert, bis sie bei einem regulären Update mit explizitem `tax_year` neu geschrieben werden.

## Frontend-Flow

Personen-CRUD läuft lokal über:

`frontend-web -> api-gateway -> person-service -> MongoDB`

## Entwicklung

```bash
uv sync --all-packages --dev
PYTHONPATH=services/person-service:shared/src uv run --all-packages pytest services/person-service/tests/test_person_api.py
```
