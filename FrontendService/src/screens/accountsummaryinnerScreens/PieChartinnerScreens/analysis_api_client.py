import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)


class AnalysisApiClient:
    """Kleiner Frontend-Helper für die Company-Analyse-Endpoints."""

    def __init__(self, base_url: str):
        self.base_url = (base_url or "").rstrip("/")

    def _get(self, path: str, params: dict[str, Any] | None = None) -> tuple[dict[str, Any] | None, str | None]:
        url = f"{self.base_url}{path}"
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            payload = response.json()
            if isinstance(payload, dict):
                return payload, None
            return {"data": payload}, None
        except requests.HTTPError as exc:
            status_code = exc.response.status_code if exc.response is not None else "unknown"
            logger.error("AnalysisApiClient HTTP-Fehler bei %s: %s", url, status_code)
            return None, f"API-Fehler ({status_code}) beim Laden von {path}"
        except requests.RequestException as exc:
            logger.error("AnalysisApiClient Request-Fehler bei %s: %s", url, exc)
            return None, "Netzwerkfehler beim Laden der Analyse-Daten"
        except ValueError:
            logger.exception("AnalysisApiClient JSON-Fehler bei %s", url)
            return None, "Ungültige Serverantwort"

    def load_snapshot(self, isin: str):
        return self._get(f"/analysis/company/{isin}/snapshot")

    def load_full(self, isin: str):
        return self._get(f"/analysis/company/{isin}/full")

    def load_company_analysis(self, isin: str) -> tuple[dict[str, Any], list[str]]:
        """Lädt Snapshot + Full und merged die wichtigsten Blöcke robust zusammen."""
        warnings: list[str] = []
        snapshot, snapshot_error = self.load_snapshot(isin)
        full, full_error = self.load_full(isin)

        if snapshot_error:
            warnings.append(f"Snapshot: {snapshot_error}")
        if full_error:
            warnings.append(f"Full: {full_error}")

        merged: dict[str, Any] = {}
        for block in (snapshot or {}, full or {}):
            if isinstance(block, dict):
                merged.update(block)

        for section in ("instrument", "market", "profile", "timeseries"):
            left = snapshot.get(section) if isinstance(snapshot, dict) else None
            right = full.get(section) if isinstance(full, dict) else None
            if isinstance(left, dict) or isinstance(right, dict):
                merged[section] = {}
                if isinstance(left, dict):
                    merged[section].update(left)
                if isinstance(right, dict):
                    merged[section].update(right)

        return merged, warnings

    def load_financials(self, isin: str, period: str):
        return self._get(f"/analysis/company/{isin}/financials", params={"period": period})

    def load_analysts(self, isin: str):
        return self._get(f"/analysis/company/{isin}/analysts")

    def load_fund(self, isin: str):
        return self._get(f"/analysis/company/{isin}/fund")

    def load_risk(self, isin: str, benchmark: str):
        return self._get(f"/analysis/company/{isin}/risk", params={"benchmark": benchmark})

    def load_benchmark(self, isin: str, benchmark: str):
        return self._get(f"/analysis/company/{isin}/benchmark", params={"benchmark": benchmark})

    def load_timeseries(self, isin: str, series: str, benchmark: str | None = None):
        params = {"series": series}
        if benchmark:
            params["benchmark"] = benchmark
        return self._get(f"/analysis/company/{isin}/timeseries", params=params)
