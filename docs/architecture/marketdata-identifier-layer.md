# Marketdata Identifier Layer (OpenFIGI)

## Ziel

Die Identifier-Auflösung ist vom reinen Marketdata-Abruf getrennt:

- **yfinance** liefert Markt- und Snapshotdaten (Suche, Selection, Preise, Summary).
- **OpenFIGI** wird ausschließlich für Identifier-Auflösung (insb. `isin`, optional `wkn`/`figi`) verwendet.

Damit bleibt die Provider-Verantwortung klar getrennt und testbar.

## Service-Grenzen

- **marketdata-service**
  - Verantwortlich für Identifier-Resolution + lokales Identity-Caching.
  - Persistiert Security-Identity-Daten lokal (`marketdata_security_identity`).
- **api-gateway**
  - Bleibt dünn: orchestriert bei Holding-Anlage optional einen Selection-Lookup, um vorhandene Identifier (`isin`, `wkn`) mitzunehmen.
  - Keine OpenFIGI-spezifische Logik, keine direkte Provider-Integration.
- **portfolio-service**
  - Bleibt rein fachlich für Holdings zuständig.
  - `isin` und `wkn` bleiben optional; fehlende Identifier blockieren kein Create.

## Neue/ relevante Settings (marketdata-service)

- `IDENTIFIER_RESOLVER` (`none` | `openfigi` | `auto`)
- `OPENFIGI_ENABLED` (`true`/`false`)
- `OPENFIGI_API_KEY` (optional, benötigt für produktive OpenFIGI-Nutzung)
- `OPENFIGI_BASE_URL` (Default: `https://api.openfigi.com/v3`)
- `OPENFIGI_REQUEST_TIMEOUT_SECONDS`
- `MARKETDATA_SECURITY_IDENTITY_COLLECTION`

## Lokale Entwicklung

Beispiel (nur wenn OpenFIGI lokal getestet werden soll):

```bash
export IDENTIFIER_RESOLVER=openfigi
export OPENFIGI_ENABLED=true
export OPENFIGI_API_KEY="<dein-key>"
```

Ohne diese Variablen bleibt die Anwendung funktionsfähig (Resolver degradiert auf `Noop`; Search/Selection laufen weiter über yfinance).
