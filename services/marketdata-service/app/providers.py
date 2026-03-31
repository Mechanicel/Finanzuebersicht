from __future__ import annotations

from datetime import date, timedelta
from typing import Protocol

from app.models import (
    BenchmarkOption,
    DataInterval,
    DataRange,
    FundamentalsBlock,
    InstrumentDataBlocksResponse,
    InstrumentFullResponse,
    InstrumentSearchItem,
    InstrumentSummary,
    MetricsBlock,
    PricePoint,
    RiskBlock,
    SnapshotBlock,
)


class MarketDataProvider(Protocol):
    def get_instrument_summary(self, symbol: str) -> InstrumentSummary | None: ...

    def get_price_series(
        self, symbol: str, data_range: DataRange, interval: DataInterval
    ) -> list[PricePoint] | None: ...

    def get_instrument_blocks(self, symbol: str) -> InstrumentDataBlocksResponse | None: ...

    def get_instrument_full(self, symbol: str) -> InstrumentFullResponse | None: ...

    def search_instruments(self, query: str, limit: int) -> list[InstrumentSearchItem]: ...

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
                    display_name="Apple",
                    wkn="865985",
                    exchange="NASDAQ",
                    currency="USD",
                    quote_type="equity",
                    asset_type="stock",
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
                    display_name="Microsoft",
                    wkn="870747",
                    exchange="NASDAQ",
                    currency="USD",
                    quote_type="equity",
                    asset_type="stock",
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
                    display_name="MSCI World ETF",
                    wkn="A1C22M",
                    exchange="NYSEARCA",
                    currency="USD",
                    quote_type="etf",
                    asset_type="fund",
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

        self._search_index: list[InstrumentSearchItem] = [
            InstrumentSearchItem(
                symbol=instrument["summary"].symbol,
                company_name=instrument["summary"].company_name,
                display_name=instrument["summary"].display_name,
                isin=instrument["summary"].isin,
                wkn=instrument["summary"].wkn,
                exchange=instrument["summary"].exchange,
                currency=instrument["summary"].currency,
                quote_type=instrument["summary"].quote_type,
                asset_type=instrument["summary"].asset_type,
                last_price=instrument["snapshot"].last_price,
                country=instrument["summary"].country,
                sector=instrument["summary"].sector,
            )
            for instrument in self._instruments.values()
        ]

    def get_instrument_summary(self, symbol: str) -> InstrumentSummary | None:
        key = symbol.upper()
        instrument = self._instruments.get(key)
        if instrument is None:
            return None
        return instrument["summary"]

    def get_price_series(
        self, symbol: str, data_range: DataRange, interval: DataInterval
    ) -> list[PricePoint] | None:
        key = symbol.upper()
        instrument = self._instruments.get(key)
        if instrument is None:
            return None
        return self._build_prices(base=instrument["base_price"], data_range=data_range, interval=interval)

    def get_instrument_blocks(self, symbol: str) -> InstrumentDataBlocksResponse | None:
        key = symbol.upper()
        instrument = self._instruments.get(key)
        if instrument is None:
            return None
        return InstrumentDataBlocksResponse(
            symbol=instrument["summary"].symbol,
            snapshot=instrument["snapshot"],
            fundamentals=instrument["fundamentals"],
            metrics=instrument["metrics"],
            risk=instrument["risk"],
        )

    def get_instrument_full(self, symbol: str) -> InstrumentFullResponse | None:
        key = symbol.upper()
        instrument = self._instruments.get(key)
        if instrument is None:
            return None
        return InstrumentFullResponse(
            summary=instrument["summary"],
            snapshot=instrument["snapshot"],
            fundamentals=instrument["fundamentals"],
            metrics=instrument["metrics"],
            risk=instrument["risk"],
        )

    def search_instruments(self, query: str, limit: int) -> list[InstrumentSearchItem]:
        normalized = query.strip().lower()
        if not normalized:
            return []
        matches = [
            item
            for item in self._search_index
            if normalized in item.symbol.lower()
            or normalized in item.company_name.lower()
            or (item.display_name and normalized in item.display_name.lower())
            or (item.isin and normalized in item.isin.lower())
            or (item.wkn and normalized in item.wkn.lower())
        ]
        return matches[:limit]

    def list_benchmark_options(self) -> list[BenchmarkOption]:
        return list(self._benchmarks)

    @staticmethod
    def _build_prices(*, base: float, data_range: DataRange, interval: DataInterval) -> list[PricePoint]:
        trading_days = {
            DataRange.ONE_MONTH: 21,
            DataRange.THREE_MONTHS: 63,
            DataRange.SIX_MONTHS: 126,
            DataRange.ONE_YEAR: 252,
            DataRange.THREE_YEARS: 252 * 3,
            DataRange.FIVE_YEARS: 252 * 5,
        }[data_range]
        step_days = {
            DataInterval.ONE_DAY: 1,
            DataInterval.ONE_WEEK: 7,
            DataInterval.ONE_MONTH: 30,
        }[interval]
        points = max(1, trading_days // step_days)

        today = date.today()
        series: list[PricePoint] = []
        for idx in range(points):
            distance = points - idx
            wave = (distance % 11) * 0.35
            trend = idx * 0.03
            close = round(base + trend - wave, 2)
            series.append(PricePoint(date=today - timedelta(days=distance * step_days), close=close))
        return series
