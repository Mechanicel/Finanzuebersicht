# Architekturübersicht

## Systemübersicht

Die Finanzübersicht wird als verteiltes, serviceorientiertes System in einem Monorepo aufgebaut.
Ein dediziertes Web-Frontend konsumiert ein API-Gateway (BFF), das Anfragen an fachlich getrennte Microservices delegiert.

## Zielservices

1. **api-gateway**
   - Einheitlicher Einstiegspunkt für das Frontend
   - Request-Orchestrierung, Aggregation und API-Komposition

2. **masterdata-service**
   - Verwaltung von Stammdaten (Banken, Kontotypen, Referenzwerte)

3. **person-service**
   - Personenstammdaten, Bankzuordnungen und Freibeträge

4. **account-service**
   - Kontenverwaltung und manuelle Snapshot-Erfassung

5. **portfolio-service**
   - Depotkonten und Bestände (Holdings)

6. **marketdata-service**
   - Markt- und Wertpapierdaten als spezialisierter Datendienst

7. **analytics-service**
   - Aggregationen, Readmodels, Chart-Daten und Forecast-Vorbereitung

## Verantwortlichkeiten

- **Frontend**: reine Darstellung, keine Domänenlogik.
- **Gateway**: frontend-zentrierte API-Verträge, Komposition mehrerer Services.
- **Domänenservices**: klare fachliche Ownership pro Kontext.
- **Shared-Paket**: gemeinsame Datentypen (Pydantic), Utilities und Konventionen.

## Kommunikationsfluss

1. Das Frontend sendet Anfragen an das API-Gateway.
2. Das Gateway delegiert an einen oder mehrere Domänenservices.
3. Domänenservices liefern normalisierte Antworten zurück.
4. Das Gateway aggregiert bei Bedarf und liefert frontend-optimierte Responses.
5. Der Analytics-Service erzeugt aus Primärdaten konsumierbare Readmodels für UI und Reports.

