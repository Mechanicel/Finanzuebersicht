# portfolio-service

FastAPI-Service für **Depotbestände (Holdings)** und **Stichtags-Snapshots**.

## Fachliche Trennung: Bestand vs. Bewertung

Der Service speichert ausschließlich:
- rohe Bestände (`isin`, `quantity`, optional `instrument_name`),
- Snapshot-Stände je Stichtag.

Der Service speichert **keine Marktpreise** und keine implizite Bewertungslogik.
Bewertungen/Valuation erfolgen in nachgelagerten Services (z. B. analytics-service mit marketdata-service).

## API (Vue-Frontend-freundlich)

Basis: `/api/v1`

- `GET /portfolios/{portfolio_id}`
- `GET /accounts/{account_id}/portfolio`
- `PUT /accounts/{account_id}/portfolio/holdings`
- `GET /accounts/{account_id}/portfolio/holdings`
- `POST /accounts/{account_id}/portfolio/snapshots`
- `GET /accounts/{account_id}/portfolio/snapshots`

Response-Felder für UI-Komponenten:
- `display_name`
- `account_summary`
- `holdings_count`
- `latest_snapshot_summary`
- `total_quantity_summary`

### Query-Parameter

- `as_of=YYYY-MM-DD` (Snapshot-Historie bis Stichtag)
- `include_history=true|false` (z. B. nur letzte Momentaufnahme)
- `response_mode=detailed|compact` (Liste vollständig vs. kompakt für Overview-Karten)

## Validierungen

- ISIN-Format via Regex
- `quantity > 0`
- keine Dubletten-ISIN innerhalb eines Holdings-Updates
- keine Dubletten-ISIN innerhalb eines Snapshot-Posts
- leere Holdings-Listen werden abgewiesen

## Hinweise zur Vue-Integration

- **Listenansicht Depot:** `GET /accounts/{account_id}/portfolio/holdings` (detailed)
- **Bearbeitungsformular Holdings:** Formularwerte auf `PUT /accounts/{account_id}/portfolio/holdings`
- **Detailseite Portfolio:** `GET /accounts/{account_id}/portfolio` mit `include_history=true`
- **Historienansicht Snapshots:** `GET /accounts/{account_id}/portfolio/snapshots` mit `as_of`/`include_history`

## Legacy-Bereinigung

Das Legacy-Konzept `DepotDetails` ist in diesem Service nicht vorhanden.
Es gibt keine gemischten Felder, die Rohbestände und Bewertung kombinieren.
