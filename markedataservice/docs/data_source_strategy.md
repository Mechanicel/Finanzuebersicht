# Datenquellen-Strategie (Phase Analyse/Metrics)

## Ziel
Dieses Dokument definiert je Datenblock, ob Yahoo Finance (yfinance) ausreichend ist,
wo Lücken bestehen und welche Fallback-Quelle in einer Hybrid-Strategie vorgesehen ist.

## Zusammenfassung
| Datenblock | Yahoo-Status | Risiko/Lücke | Geplanter Fallback |
|---|---|---|---|
| Instrument-Metadaten (Symbol, Name, Exchange, Currency) | Gut | Regionale ISIN-Suche gelegentlich unzuverlässig | OpenFIGI + Stooq-Symbolmapping |
| Preiszeitreihen (Daily, 10y) | Gut für Standardwerte | Einzelne Delistings / Corporate-Action-Konsistenz | Stooq (gratis CSV) als Backup für Daily-Close |
| Benchmark-Zeitreihen (MSCI/S&P/FTSE-Proxy) | Gut über Ticker/ETF-Proxies | Index-Ticker können API-seitig limitiert sein | Stooq oder Alpha Vantage (gratis Tier) |
| Fundamentaldaten (Margins, ROE/ROA, Ratios) | Mittel | Felder teilweise null/inkonsistent je Listing | FinancialModelingPrep free tier (selektiv) |
| Finanzstatements (Income/Balance/Cashflow) | Mittel | Spaltenbezeichnungen und Coverage variieren | SEC EDGAR/XBRL (US), EODHD/Polygon (paid optional) |
| Analysten-/Schätzdaten | Mittel bis schwach | Nicht überall verfügbar, Zeitverzug | Finnhub free tier (limitierte Calls) |
| Fonds-/ETF-Holdings | Mittel | Holdings oft lückenhaft | issuer APIs / justETF scraping (Phase 5, legal check) |

## Architekturvorbereitung im Code
- Provider-Schnittstelle enthält jetzt explizit `fetch_benchmark_timeseries(symbol)`.
- Analyse-Layer greift ausschließlich über Provider-Schnittstellen auf Benchmarks zu.
- Dadurch kann ein zweiter Provider später per Router/Fallback eingefügt werden,
  ohne Endpunkte oder Metrikformeln anzupassen.

## Phase-4/5 Integrationsplan
1. **ProviderRouter einführen** (primary + fallback chain je Datenblock).
2. **Fallback aktivieren für Benchmark/Price** (niedriges Risiko, hoher Nutzen).
3. **Fundamental-Fallback selektiv** für `None`-Felder (margin/ratios).
4. **Quellen-Metadaten je Kennzahl** auf Blockebene präzisieren (hybrid source map).

## Qualitätsregeln
- Backend liefert immer `value`, `unit`, `as_of`, `source` pro Kennzahl.
- Frontend konsumiert Kennzahlen nur, berechnet sie nicht.
- Fehlende Werte werden als `null` geliefert (kein stilles Frontend-Fallback).
