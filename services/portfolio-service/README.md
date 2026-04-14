# portfolio-service

FastAPI-Service für **Portfolio- und Holding-Erfassung**.

## Service-Grenzen

Der `portfolio-service` speichert nur Bestands-/Kaufdaten (z. B. `quantity`, `acquisition_price`, `buy_date`) und **keine laufenden Marktpreise**.
Suche und aktuelle Kurse kommen weiterhin aus dem `marketdata-service`.

## API (Basis `/api/v1`)

- `POST /portfolios` – Portfolio anlegen (`person_id`, `display_name`)
- `GET /persons/{person_id}/portfolios` – Portfolios einer Person listen
- `GET /portfolios/{portfolio_id}` – Portfolio inkl. Holdings laden
- `POST /portfolios/{portfolio_id}/holdings` – Holding hinzufügen
- `PATCH /portfolios/{portfolio_id}/holdings/{holding_id}` – Holding aktualisieren
- `DELETE /portfolios/{portfolio_id}/holdings/{holding_id}` – Holding löschen

## Persistenz-Konfiguration

Standard ist MongoDB:

- `PORTFOLIO_REPOSITORY_BACKEND=mongo` (Default)
- `MONGO_URI` oder alternativ `MONGO_HOST`/`MONGO_PORT`/`MONGO_DATABASE` (+ optional User/Pass)
- `MONGO_PORTFOLIOS_COLLECTION` (Default `portfolios`)
- `MONGO_HOLDINGS_COLLECTION` (Default `holdings`)

Für Tests/Fallback bleibt InMemory möglich:

- `PORTFOLIO_REPOSITORY_BACKEND=inmemory`
