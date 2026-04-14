# masterdata-service

FastAPI-Service für Referenzdaten im Finanzuebersicht-Monorepo. Haupt-Consumer ist das zukünftige Vue-Frontend.

## Scope

Der Service verwaltet:

- Banken (inkl. BIC/BLZ)
- Kontotypen
- Formular-/Schema-Metadaten pro Kontotyp für dynamische Vue-Formulare

## Architektur

- **Router-Layer**: HTTP-Endpunkte unter `/api/v1/*`
- **Service-Layer**: Domänenlogik (Validierung, Sortierung, Konfliktprüfung)
- **Repository-Layer**: Datenspeicher-Abstraktion (`InMemoryMasterdataRepository`)
- **Pydantic-Schemas**: stabile Request/Response-Modelle

## Starten

```bash
uv run uvicorn app.main:app --reload --app-dir services/masterdata-service
```

OpenAPI/Swagger:

- `http://localhost:8000/docs`
- `http://localhost:8000/openapi.json`

## API-Endpunkte

### Banken

- `GET /api/v1/banks`
- `POST /api/v1/banks`
- `GET /api/v1/banks/{bank_id}`
- `PATCH /api/v1/banks/{bank_id}`
- `DELETE /api/v1/banks/{bank_id}`

### Kontotypen

- `GET /api/v1/account-types`
- `POST /api/v1/account-types`
- `GET /api/v1/account-types/{account_type_id}`
- `PATCH /api/v1/account-types/{account_type_id}`
- `DELETE /api/v1/account-types/{account_type_id}`

## Datenmodell

### Bank

```json
{
  "bank_id": "uuid",
  "name": "string",
  "bic": "MARKDEF1100",
  "blz": "12345678",
  "country_code": "DE"
}
```

### AccountType

```json
{
  "account_type_id": "uuid",
  "key": "girokonto",
  "name": "Girokonto",
  "description": "optional",
  "schema_fields": [
    {
      "feldname": "waehrung",
      "label": "Währung",
      "typ": "select",
      "required": true,
      "placeholder": null,
      "default": "EUR",
      "options": [
        {"value": "EUR", "label": "Euro"},
        {"value": "USD", "label": "US Dollar"}
      ],
      "help_text": "optional",
      "order": 10
    }
  ]
}
```

`schema_fields` werden serverseitig nach `order` sortiert zurückgegeben.

## Vue-Frontend: Schema-Konsum für dynamische Formulare

1. Kontotypen laden via `GET /api/v1/account-types`.
2. Für den ausgewählten Kontotyp `schema_fields` verwenden.
3. Pro Feld:
   - `feldname` → `v-model` Key
   - `label`/`help_text` → UI-Beschriftung
   - `typ` → Vue-Komponente (z. B. text/select/date)
   - `required` → Validierungsregel
   - `placeholder`/`default` → Initialisierung
   - `options` → Select-Optionen
   - `order` → Render-Reihenfolge
4. Payload an Folge-Services (z. B. account-service) im Objektformat senden.

Damit ist das Schema direkt formularfähig, ohne Frontend-Mapping auf Legacy-Seed-Strukturen.

## Validierungsregeln (Auszug)

- BIC: 8 oder 11 alphanumerische Zeichen (uppercase)
- BLZ: exakt 8 Ziffern
- Bank-BIC und Bank-BLZ sind jeweils eindeutig
- `schema_fields[].feldname` innerhalb eines Kontotyps eindeutig
- `typ=select` erfordert mindestens eine Option
- `options` sind nur für `typ=select` erlaubt

## Tests

```bash
pytest services/masterdata-service/tests -q
```

## Legacy-Hinweis

Der Service verwendet **keine** `banken.json`/`kontotypen.json`-Seeds als aktive Datenquelle.
