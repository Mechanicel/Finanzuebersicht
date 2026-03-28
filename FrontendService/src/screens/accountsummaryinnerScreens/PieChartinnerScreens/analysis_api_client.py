import logging
import time
from typing import Any

import requests
from finanzuebersicht_shared import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class AnalysisApiClient:
    """Kleiner Frontend-Helper für die Company-Analyse-Endpoints."""

    def __init__(self, base_url: str):
        self.base_url = (base_url or "").rstrip("/")
        self._cache: dict[tuple[str, tuple[tuple[str, Any], ...]], tuple[dict[str, Any] | None, str | None]] = {}
        self.request_count = 0

    def _cache_key(self, path: str, params: dict[str, Any] | None = None) -> tuple[str, tuple[tuple[str, Any], ...]]:
        normalized = tuple(sorted((str(k), str(v)) for k, v in (params or {}).items() if v is not None))
        return path, normalized

    def _get(self, path: str, params: dict[str, Any] | None = None) -> tuple[dict[str, Any] | None, str | None]:
        url = f"{self.base_url}{path}"
        start = time.perf_counter()
        self.request_count += 1
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            payload = response.json()
            if settings.performance_logging:
                duration_ms = (time.perf_counter() - start) * 1000
                logger.info("GET %s took %.0fms", path, duration_ms)
            if isinstance(payload, dict):
                return payload, None
            return {"data": payload}, None
        except requests.HTTPError as exc:
            status_code = exc.response.status_code if exc.response is not None else "unknown"
            if settings.performance_logging:
                duration_ms = (time.perf_counter() - start) * 1000
                logger.info("GET %s took %.0fms (status=%s)", path, duration_ms, status_code)
            logger.error("AnalysisApiClient HTTP-Fehler bei %s: %s", url, status_code)
            return None, f"API-Fehler ({status_code}) beim Laden von {path}"
        except requests.RequestException as exc:
            if settings.performance_logging:
                duration_ms = (time.perf_counter() - start) * 1000
                logger.info("GET %s took %.0fms (request_error)", path, duration_ms)
            logger.error("AnalysisApiClient Request-Fehler bei %s: %s", url, exc)
            return None, "Netzwerkfehler beim Laden der Analyse-Daten"
        except ValueError:
            if settings.performance_logging:
                duration_ms = (time.perf_counter() - start) * 1000
                logger.info("GET %s took %.0fms (json_error)", path, duration_ms)
            logger.exception("AnalysisApiClient JSON-Fehler bei %s", url)
            return None, "Ungültige Serverantwort"

    def _cached_get(self, path: str, params: dict[str, Any] | None = None) -> tuple[dict[str, Any] | None, str | None]:
        key = self._cache_key(path, params)
        if key in self._cache:
            return self._cache[key]

        result = self._get(path, params=params)
        self._cache[key] = result
        return result

    def load_snapshot(self, isin: str):
        return self._cached_get(f"/analysis/company/{isin}/snapshot")

    def load_full(self, isin: str):
        return self._cached_get(f"/analysis/company/{isin}/full")

    def load_fundamentals(self, isin: str):
        return self._cached_get(f"/analysis/company/{isin}/fundamentals")

    def load_metrics(self, isin: str):
        return self._cached_get(f"/analysis/company/{isin}/metrics")

    def load_risk(self, isin: str, benchmark: str | None = None):
        params = {"benchmark": benchmark} if benchmark else None
        return self._cached_get(f"/analysis/company/{isin}/risk", params=params)

    def load_benchmark(self, isin: str, benchmark: str | None = None):
        params = {"benchmark": benchmark} if benchmark else None
        return self._cached_get(f"/analysis/company/{isin}/benchmark", params=params)

    def load_timeseries(self, isin: str, series: str, benchmark: str | None = None):
        params = {"series": series}
        if benchmark:
            params["benchmark"] = benchmark
        return self._cached_get(f"/analysis/company/{isin}/timeseries", params=params)

    def load_financials(self, isin: str, period: str):
        return self._cached_get(f"/analysis/company/{isin}/financials", params={"period": period})

    def load_benchmark_catalog(self):
        candidates = ["/analysis/benchmark-catalog", "/analysis/benchmarks"]
        errors: list[str] = []
        for path in candidates:
            payload, warning = self._cached_get(path)
            if payload and not warning:
                return payload, None
            if warning:
                errors.append(warning)
        if errors:
            return None, " | ".join(errors)
        return None, "Benchmark-Katalog derzeit nicht verfügbar"

    def search_benchmark_candidates(self, query: str):
        normalized = (query or "").strip()
        if not normalized:
            return {"results": []}, None
        return self._cached_get("/analysis/benchmark-search", params={"q": normalized})

    def load_comparison_timeseries(self, isin: str, symbols: list[str]):
        normalized = sorted({str(symbol).strip().upper() for symbol in (symbols or []) if str(symbol).strip()})
        if not normalized:
            return {"company": {"isin": isin, "series": []}, "comparisons": []}, None
        params = {"symbols": ",".join(normalized)}
        return self._cached_get(f"/analysis/company/{isin}/comparison-timeseries", params=params)

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

    def load_analysts(self, isin: str):
        return self._cached_get(f"/analysis/company/{isin}/analysts")

    def load_fund(self, isin: str):
        return self._cached_get(f"/analysis/company/{isin}/fund")
