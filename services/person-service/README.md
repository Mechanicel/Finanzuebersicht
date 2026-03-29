# person-service

Eigenständiger FastAPI-Service für Personen, Person↔Bank-Zuordnungen und Freibeträge.

## Architektur

Der Service modelliert die Domäne **entkoppelt** in drei Ressourcen:

- `Person`
- `PersonBankAssignment`
- `TaxAllowance`

Es gibt **keine** eingebetteten Legacy-Gesamtdokumente und **keine** implizite Kopplung zum `account-service`.

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

## Frontend-freundliche Response-Struktur

Alle Endpunkte liefern das Standard-Envelope-Format:

```json
{
  "data": { "...": "..." },
  "request_id": "...",
  "correlation_id": "..."
}
```

- Listenendpunkte liefern `items` plus Metadaten (`pagination` oder `total`).
- Detailendpunkt liefert `person` plus `stats`.
- Summary-Endpunkt liefert `banks[]` und `total_amount` explizit.

## Validierungen

- Doppelte Person (`first_name + last_name + email`) → `409`
- Doppelte Person↔Bank-Zuordnung → `409`
- Freibetrag nur bei bestehender Person↔Bank-Zuordnung → `409`

## Entwicklung

```bash
pytest services/person-service/tests -q
```
