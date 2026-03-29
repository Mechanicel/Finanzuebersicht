from __future__ import annotations

from datetime import date, timedelta
from typing import Protocol

from app.models import (
    BenchmarkOption,
    DataRange,
    PricePoint,
    ProviderInstrumentData,
    FundamentalsBlock,
    InstrumentSummary,
    MetricsBlock,
    RiskBlock,
    SnapshotBlock,
)


class MarketDataProvider(Protocol):
    def get_instrument_data(self, symbol: str, data_range: DataRange) -> ProviderInstrumentData | None: ...

    def list_benchmark_options(self) -> list[BenchmarkOption]: ...


class InMemoryMarketDataProvider:
    def __init__(self) -> None:
        self._benchmarks = [
            BenchmarkOption(
                benchmark_id="sp500",
                symbol="^GSPC",
                label="S&P 500",
                region="US",
                asset_class="equity",
            ),
            BenchmarkOption(
                benchmark_id="msci_world",
                symbol="URTH",
                label="MSCI World ETF Proxy",
                region="Global",
                asset_class="equity",
            ),
            BenchmarkOption(
                benchmark_id="dax",
                symbol="^GDAXI",
                label="DAX",
                region="DE",
                asset_class="equity",
            ),
        ]

        self._instruments: dict[str, dict] = {
            "AAPL": {
                "summary": InstrumentSummary(
                    symbol="AAPL",
                    isin="US0378331005",
                    company_name="Apple Inc.",
                    exchange="NASDAQ",
                    currency="USD",
                    country="US",
                    sector="Technology",
                    industry="Consumer Electronics",
                ),
                "base_price": 182.0,
                "snapshot": SnapshotBlock(last_price=189.32, change_1d_pct=1.21, volume=52_310_200),
                "fundamentals": FundamentalsBlock(
                    market_cap=2_900_000_000_000,
                    pe_ratio=29.1,
                    dividend_yield=0.45,
                    revenue_growth_yoy=0.071,
                ),
                "metrics": MetricsBlock(sma_50=186.11, sma_200=178.44, rsi_14=56.2),
                "risk": RiskBlock(beta=1.08, volatility_30d=0.22, max_drawdown_1y=-0.17, value_at_risk_95_1d=-0.026),
            },
            "MSFT": {
                "summary": InstrumentSummary(
                    symbol="MSFT",
                    isin="US5949181045",
                    company_name="Microsoft Corp.",
                    exchange="NASDAQ",
                    currency="USD",
                    country="US",
                    sector="Technology",
                    industry="Software",
                ),
                "base_price": 402.0,
                "snapshot": SnapshotBlock(last_price=410.91, change_1d_pct=0.78, volume=24_910_010),
                "fundamentals": FundamentalsBlock(
                    market_cap=3_100_000_000_000,
                    pe_ratio=34.7,
                    dividend_yield=0.68,
                    revenue_growth_yoy=0.123,
                ),
                "metrics": MetricsBlock(sma_50=406.35, sma_200=387.2, rsi_14=59.8),
                "risk": RiskBlock(beta=0.93, volatility_30d=0.19, max_drawdown_1y=-0.13, value_at_risk_95_1d=-0.021),
            },
            "URTH": {
                "summary": InstrumentSummary(
                    symbol="URTH",
                    isin="US4642863926",
                    company_name="iShares MSCI World ETF",
                    exchange="NYSEARCA",
                    currency="USD",
                    country="Global",
                    sector="ETF",
                    industry="World Equity",
                ),
                "base_price": 135.0,
                "snapshot": SnapshotBlock(last_price=137.5, change_1d_pct=0.3, volume=2_120_400),
                "fundamentals": FundamentalsBlock(
                    market_cap=3_700_000_000,
                    pe_ratio=21.3,
                    dividend_yield=1.75,
                    revenue_growth_yoy=None,
                ),
                "metrics": MetricsBlock(sma_50=136.2, sma_200=132.4, rsi_14=53.1),
                "risk": RiskBlock(beta=1.0, volatility_30d=0.14, max_drawdown_1y=-0.11, value_at_risk_95_1d=-0.017),
            },
        }

    def get_instrument_data(self, symbol: str, data_range: DataRange) -> ProviderInstrumentData | None:
        key = symbol.upper()
        instrument = self._instruments.get(key)
        if instrument is None:
            return None

        return ProviderInstrumentData(
            summary=instrument["summary"],
            prices=self._build_prices(base=instrument["base_price"], data_range=data_range),
            snapshot=instrument["snapshot"],
            fundamentals=instrument["fundamentals"],
            metrics=instrument["metrics"],
            risk=instrument["risk"],
        )

    def list_benchmark_options(self) -> list[BenchmarkOption]:
        return list(self._benchmarks)

    @staticmethod
    def _build_prices(*, base: float, data_range: DataRange) -> list[PricePoint]:
        points = {
            DataRange.ONE_MONTH: 21,
            DataRange.THREE_MONTHS: 63,
            DataRange.SIX_MONTHS: 126,
            DataRange.ONE_YEAR: 252,
            DataRange.THREE_YEARS: 252 * 3,
            DataRange.FIVE_YEARS: 252 * 5,
        }[data_range]

        today = date.today()
        series: list[PricePoint] = []
        for idx in range(points):
            distance = points - idx
            wave = (distance % 11) * 0.35
            trend = idx * 0.03
            close = round(base + trend - wave, 2)
            series.append(PricePoint(date=today - timedelta(days=distance), close=close))
        return series
