from src.services.analysis_service import AnalysisMetricsService
from src.models.stock_model import StockModel


class DummyProvider:
    provider_name = "dummy"

    def fetch_benchmark_timeseries(self, symbol: str):
        return [
            {"date": "2026-03-20", "close": 100.0},
            {"date": "2026-03-21", "close": 101.0},
            {"date": "2026-03-24", "close": 103.0},
        ]


def _model() -> StockModel:
    return StockModel(
        isin="DE000BASF111",
        price_history=[
            {"date": "2026-03-20", "close": 50.0},
            {"date": "2026-03-21", "close": 51.0},
            {"date": "2026-03-24", "close": 53.0},
        ],
        meta={
            "provider_map": {"timeseries": "dummy"},
            "financials": {
                "income_statement": {
                    "annual": [
                        {
                            "date": "2024-12-31",
                            "Total Revenue": 1000.0,
                            "Gross Profit": 400.0,
                            "Operating Income": 150.0,
                            "Net Income": 100.0,
                            "Diluted Average Shares": 50.0,
                        },
                        {
                            "date": "2025-12-31",
                            "Total Revenue": 1100.0,
                            "Gross Profit": 450.0,
                            "Operating Income": 180.0,
                            "Net Income": 120.0,
                            "Diluted Average Shares": 50.0,
                        },
                    ]
                }
            },
        },
        balance_sheet={
            "annual": [
                {
                    "date": "2025-12-31",
                    "Stockholders Equity": 500.0,
                    "Total Assets": 1200.0,
                    "Total Debt": 300.0,
                    "Current Assets": 350.0,
                    "Current Liabilities": 200.0,
                    "Cash And Cash Equivalents": 80.0,
                    "Receivables": 70.0,
                }
            ],
            "snapshot": {"totalDebt": 300.0, "totalCash": 80.0},
        },
        cash_flow={
            "annual": [
                {"date": "2024-12-31", "Free Cash Flow": 90.0},
                {"date": "2025-12-31", "Free Cash Flow": 95.0},
            ]
        },
        quality={"currentRatio": 1.75, "quickRatio": 1.1},
        valuation={"totalDebt": 300.0, "totalCash": 80.0},
    )


def test_metrics_payload_contains_required_groups():
    service = AnalysisMetricsService(DummyProvider())

    payload = service.build_metrics_payload(_model())

    assert "performance" in payload
    assert "growth" in payload
    assert "profitability" in payload
    assert "balance_sheet" in payload
    assert payload["performance"]["total_return"]["value"] is not None


def test_benchmark_payload_contains_timeseries_and_excess_return():
    service = AnalysisMetricsService(DummyProvider())

    payload = service.build_benchmark_payload(_model(), benchmark_key="sp500")

    assert payload["benchmark"]["key"] == "sp500"
    assert payload["timeseries"]["relative"]
    assert payload["comparison"]["excess_return"]["value"] is not None
