from __future__ import annotations

import datetime

from src.main import create_app
from src.services.stock_service import InstrumentNotFoundError
import src.api.stock as stock_api


class FakeStockService:
    def get_company(self, isin: str) -> str:
        if isin == "DE000BASF111":
            return "BASF SE"
        raise InstrumentNotFoundError("Kein Instrument gefunden")

    def get_price(self, isin: str, target_date: datetime.date | None) -> float:
        if isin != "DE000BASF111":
            raise InstrumentNotFoundError("Kein Instrument gefunden")
        if target_date is None:
            return 51.0
        if target_date == datetime.date(2026, 3, 20):
            return 49.5
        if target_date == datetime.date(2026, 3, 22):
            return 49.5
        return 48.0

    def get_analysis_metrics(self, isin: str):
        return {"metrics": {"performance": {"volatility": {"value": 0.2}}}}

    def get_analysis_risk(self, isin: str, benchmark_key: str | None = None):
        return {"risk": {"beta": {"value": 1.1}}, "benchmark": {"key": benchmark_key or "msci_world"}}

    def get_analysis_benchmark(self, isin: str, benchmark_key: str | None = None):
        return {"comparison": {"excess_return": {"value": 0.05}}, "benchmark": {"key": benchmark_key or "msci_world"}}

    def get_analysis_timeseries(self, isin: str, series: str, benchmark_key: str | None = None):
        return {"series": {"price": [{"date": "2026-03-24", "close": 51.0}]}, "benchmark": {"key": benchmark_key or "msci_world"}}

    def get_analysis_benchmark_catalog(self):
        return {
            "benchmarks": {
                "msci_world": {"label": "MSCI World"},
                "sp500": {"label": "S&P 500"},
                "ftse_all_world": {"label": "FTSE All-World"},
            },
            "default": "msci_world",
            "meta": {"source": "fake"},
        }


def _client():
    stock_api.service = FakeStockService()
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def test_company_endpoint_for_valid_instrument():
    client = _client()

    response = client.get("/company/DE000BASF111")

    assert response.status_code == 200
    assert response.get_json()["company_name"] == "BASF SE"


def test_price_endpoint_without_date_returns_current_price():
    client = _client()

    response = client.get("/price/DE000BASF111")

    assert response.status_code == 200
    assert response.get_json()["price"] == 51.0


def test_price_endpoint_with_historical_date():
    client = _client()

    response = client.get("/price/DE000BASF111?date=2026-03-20")

    assert response.status_code == 200
    assert response.get_json()["price"] == 49.5


def test_price_endpoint_non_trading_day_uses_previous_price():
    client = _client()

    response = client.get("/price/DE000BASF111?date=2026-03-22")

    assert response.status_code == 200
    assert response.get_json()["price"] == 49.5


def test_invalid_isin_returns_404():
    client = _client()

    response = client.get("/company/INVALID")

    assert response.status_code == 404
    payload = response.get_json()
    assert payload["error"]["code"] == "not_found"


def test_invalid_date_format_returns_400():
    client = _client()

    response = client.get("/price/DE000BASF111?date=20-03-2026")

    assert response.status_code == 400
    payload = response.get_json()
    assert payload["error"]["code"] == "invalid_date"


def test_analysis_metrics_endpoint():
    client = _client()

    response = client.get("/analysis/company/DE000BASF111/metrics")

    assert response.status_code == 200
    assert response.get_json()["metrics"]["performance"]["volatility"]["value"] == 0.2


def test_analysis_risk_endpoint_with_benchmark():
    client = _client()

    response = client.get("/analysis/company/DE000BASF111/risk?benchmark=sp500")

    assert response.status_code == 200
    assert response.get_json()["benchmark"]["key"] == "sp500"


def test_analysis_benchmark_endpoint():
    client = _client()

    response = client.get("/analysis/company/DE000BASF111/benchmark?benchmark=ftse_all_world")

    assert response.status_code == 200
    assert response.get_json()["benchmark"]["key"] == "ftse_all_world"


def test_analysis_timeseries_endpoint():
    client = _client()

    response = client.get("/analysis/company/DE000BASF111/timeseries?series=price,returns")

    assert response.status_code == 200
    assert response.get_json()["series"]["price"][0]["close"] == 51.0


def test_analysis_benchmark_catalog_alias_routes_return_same_payload():
    client = _client()

    benchmark_catalog_response = client.get("/analysis/benchmark-catalog")
    benchmarks_response = client.get("/analysis/benchmarks")

    assert benchmark_catalog_response.status_code == 200
    assert benchmarks_response.status_code == 200
    assert benchmark_catalog_response.get_json() == benchmarks_response.get_json()
