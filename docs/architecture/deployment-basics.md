# Deployment Basics

## Zielbild

- Frontend als statische Vue-Build-Artefakte (z. B. CDN/Object Storage).
- FastAPI-Services containerisiert und horizontal skalierbar.
- API Gateway als stabiler Entry Point für das Web-Frontend.

## Basis-Prinzipien

1. **Frontend/Backend entkoppelt deployen**.
2. **Konfiguration per Environment Variablen** (z. B. `VITE_API_BASE_URL`, Service-URLs im Gateway).
3. **Health-Checks** für alle Services (`/health`).
4. **Rolling/Blue-Green** Deployment für API-Services.
5. **Observability**: strukturierte Logs, Request/Correlation IDs.

## Minimaler Rollout

1. Backend-Services + Gateway deployen.
2. Frontend mit korrekter Gateway-Base-URL bauen/deployen.
3. Smoke-Test: Personenliste, Dashboard, Konten, Depot-Ansichten über Gateway.
