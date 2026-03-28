import requests

from src.screens.accountsummaryinnerScreens.PieChartinnerScreens.analysis_api_client import AnalysisApiClient


class DummyResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(response=self)

    def json(self):
        return self._payload


def test_load_benchmark_catalog_prefers_new_endpoint(monkeypatch):
    calls = []

    def fake_get(url, params=None, timeout=10):
        calls.append(url)
        if url.endswith("/analysis/benchmark-catalog"):
            return DummyResponse({"benchmarks": [{"id": "SP500", "name": "S&P 500"}]})
        return DummyResponse({"benchmarks": []})

    monkeypatch.setattr(requests, "get", fake_get)
    client = AnalysisApiClient("http://marketdata")

    payload, warning = client.load_benchmark_catalog()

    assert warning is None
    assert payload["benchmarks"][0]["id"] == "SP500"
    assert calls == ["http://marketdata/analysis/benchmark-catalog"]


def test_load_benchmark_catalog_falls_back_to_legacy_endpoint(monkeypatch):
    calls = []

    def fake_get(url, params=None, timeout=10):
        calls.append(url)
        if url.endswith("/analysis/benchmark-catalog"):
            return DummyResponse({"error": "not found"}, status_code=404)
        return DummyResponse({"benchmarks": ["DAX"]})

    monkeypatch.setattr(requests, "get", fake_get)
    client = AnalysisApiClient("http://marketdata")

    payload, warning = client.load_benchmark_catalog()

    assert warning is None
    assert payload["benchmarks"] == ["DAX"]
    assert calls == [
        "http://marketdata/analysis/benchmark-catalog",
        "http://marketdata/analysis/benchmarks",
    ]
