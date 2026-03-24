from __future__ import annotations

import datetime
import math
from typing import Any

from src.models.stock_model import StockModel


class AnalysisMetricsService:
    """Berechnet abgeleitete Kennzahlen aus strukturierten Rohdaten."""

    BENCHMARKS: dict[str, dict[str, str]] = {
        "msci_world": {"symbol": "URTH", "name": "MSCI World (ETF Proxy URTH)"},
        "sp500": {"symbol": "^GSPC", "name": "S&P 500"},
        "ftse_all_world": {"symbol": "VT", "name": "FTSE All-World (ETF Proxy VT)"},
    }

    def __init__(self, provider: Any):
        self.provider = provider

    def benchmark_catalog(self) -> dict[str, dict[str, str]]:
        return self.BENCHMARKS

    def benchmark_for_key(self, benchmark_key: str | None) -> tuple[str, dict[str, str]]:
        key = (benchmark_key or "msci_world").strip().lower()
        if key not in self.BENCHMARKS:
            allowed = ", ".join(sorted(self.BENCHMARKS.keys()))
            raise ValueError(f"Unknown benchmark '{benchmark_key}'. Allowed keys: {allowed}")
        return key, self.BENCHMARKS[key]

    def build_metrics_payload(self, model: StockModel) -> dict[str, Any]:
        prices = self._normalize_price_history(model.price_history)
        returns = self._daily_returns([point["close"] for point in prices])
        as_of = prices[-1]["date"] if prices else None
        source = (model.meta.get("provider_map") or {}).get("timeseries") or getattr(self.provider, "provider_name", "unknown")

        income_annual = (model.meta.get("financials") or {}).get("income_statement", {}).get("annual", [])
        balance_annual = (model.balance_sheet or {}).get("annual", [])
        cashflow_annual = (model.cash_flow or {}).get("annual", [])

        revenue_series = self._series_by_candidates(income_annual, ["Total Revenue", "Revenue", "Operating Revenue"])
        eps_series = self._eps_series(income_annual)
        fcf_series = self._series_by_candidates(cashflow_annual, ["Free Cash Flow", "FreeCashFlow"])

        latest_income = income_annual[-1] if income_annual else {}
        latest_balance = balance_annual[-1] if balance_annual else {}

        metrics = {
            "performance": {
                "volatility": self._metric(self._annualized_volatility(returns), "ratio", as_of, source),
                "sharpe_ratio": self._metric(self._sharpe_ratio(returns), "ratio", as_of, source),
                "max_drawdown": self._metric(self._max_drawdown(prices), "ratio", as_of, source),
                "cagr": self._metric(self._cagr(prices), "ratio", as_of, source),
                "total_return": self._metric(self._total_return(prices), "ratio", as_of, source),
            },
            "growth": {
                "revenue_growth": self._metric(self._latest_growth(revenue_series), "ratio", self._last_date(revenue_series), source),
                "eps_growth": self._metric(self._latest_growth(eps_series), "ratio", self._last_date(eps_series), source),
                "fcf_growth": self._metric(self._latest_growth(fcf_series), "ratio", self._last_date(fcf_series), source),
            },
            "profitability": {
                "gross_margin": self._metric(self._ratio(latest_income.get("Gross Profit"), latest_income.get("Total Revenue")), "ratio", latest_income.get("date"), source),
                "operating_margin": self._metric(self._ratio(latest_income.get("Operating Income"), latest_income.get("Total Revenue")), "ratio", latest_income.get("date"), source),
                "net_margin": self._metric(self._ratio(latest_income.get("Net Income"), latest_income.get("Total Revenue")), "ratio", latest_income.get("date"), source),
                "roe": self._metric(self._ratio(latest_income.get("Net Income"), latest_balance.get("Stockholders Equity")), "ratio", latest_income.get("date") or latest_balance.get("date"), source),
                "roa": self._metric(self._ratio(latest_income.get("Net Income"), latest_balance.get("Total Assets")), "ratio", latest_income.get("date") or latest_balance.get("date"), source),
                "roic": self._metric(self._roic(latest_income, latest_balance, model.valuation), "ratio", latest_income.get("date") or latest_balance.get("date"), source),
            },
            "balance_sheet": {
                "net_debt": self._metric(self._net_debt(model), "currency", as_of, source),
                "current_ratio": self._metric(self._first_non_null(model.quality.get("currentRatio"), self._ratio(latest_balance.get("Current Assets"), latest_balance.get("Current Liabilities"))), "ratio", latest_balance.get("date"), source),
                "quick_ratio": self._metric(self._first_non_null(model.quality.get("quickRatio"), self._quick_ratio(latest_balance)), "ratio", latest_balance.get("date"), source),
            },
        }
        return metrics

    def build_timeseries(self, model: StockModel, series_keys: list[str], benchmark_key: str | None = None) -> dict[str, Any]:
        prices = self._normalize_price_history(model.price_history)
        benchmark = self._benchmark_series(benchmark_key)
        out: dict[str, Any] = {}
        for key in series_keys:
            if key == "price":
                out["price"] = prices
            elif key == "returns":
                out["returns"] = self._returns_series(prices)
            elif key == "drawdown":
                out["drawdown"] = self._drawdown_series(prices)
            elif key == "benchmark_relative":
                out["benchmark_relative"] = self._relative_series(prices, benchmark.get("series") or [])
            elif key == "benchmark_price":
                out["benchmark_price"] = benchmark.get("series") or []
        return {
            "series": out,
            "benchmark": benchmark,
        }

    def build_risk_payload(self, model: StockModel, benchmark_key: str | None = None) -> dict[str, Any]:
        prices = self._normalize_price_history(model.price_history)
        returns = self._daily_returns([p["close"] for p in prices])
        benchmark = self._benchmark_series(benchmark_key)
        bench_returns = self._daily_returns([p["close"] for p in (benchmark.get("series") or [])])
        beta = self._beta(prices, benchmark.get("series") or []) if bench_returns else None
        as_of = prices[-1]["date"] if prices else None
        source = (model.meta.get("provider_map") or {}).get("timeseries") or getattr(self.provider, "provider_name", "unknown")

        return {
            "risk": {
                "volatility": self._metric(self._annualized_volatility(returns), "ratio", as_of, source),
                "sharpe_ratio": self._metric(self._sharpe_ratio(returns), "ratio", as_of, source),
                "max_drawdown": self._metric(self._max_drawdown(prices), "ratio", as_of, source),
                "beta": self._metric(beta, "ratio", as_of, source),
            },
            "benchmark": benchmark,
        }

    def build_benchmark_payload(self, model: StockModel, benchmark_key: str | None = None) -> dict[str, Any]:
        prices = self._normalize_price_history(model.price_history)
        benchmark = self._benchmark_series(benchmark_key)
        aligned = self._align_series(prices, benchmark.get("series") or [])
        company_ret = self._series_total_return([x[1] for x in aligned])
        bench_ret = self._series_total_return([x[2] for x in aligned])
        as_of = aligned[-1][0] if aligned else None
        source = (model.meta.get("provider_map") or {}).get("timeseries") or getattr(self.provider, "provider_name", "unknown")
        return {
            "comparison": {
                "company_total_return": self._metric(company_ret, "ratio", as_of, source),
                "benchmark_total_return": self._metric(bench_ret, "ratio", as_of, benchmark.get("source") or source),
                "excess_return": self._metric(None if company_ret is None or bench_ret is None else company_ret - bench_ret, "ratio", as_of, source),
            },
            "timeseries": {
                "relative": self._relative_series(prices, benchmark.get("series") or []),
                "company_price": prices,
                "benchmark_price": benchmark.get("series") or [],
            },
            "benchmark": benchmark,
        }

    def _benchmark_series(self, benchmark_key: str | None) -> dict[str, Any]:
        key, benchmark = self.benchmark_for_key(benchmark_key)
        series = self.provider.fetch_benchmark_timeseries(benchmark["symbol"])
        normalized = self._normalize_price_history(series)
        return {
            "key": key,
            "symbol": benchmark["symbol"],
            "name": benchmark["name"],
            "source": getattr(self.provider, "provider_name", "unknown"),
            "series": normalized,
        }

    @staticmethod
    def _first_non_null(*values: Any) -> Any:
        for value in values:
            if value is not None:
                return value
        return None

    @staticmethod
    def _metric(value: Any, unit: str, as_of: str | None, source: str) -> dict[str, Any]:
        return {"value": value, "unit": unit, "as_of": as_of, "source": source}

    @staticmethod
    def _to_float(value: Any) -> float | None:
        try:
            if value is None:
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    def _ratio(self, num: Any, den: Any) -> float | None:
        n = self._to_float(num)
        d = self._to_float(den)
        if n is None or d in (None, 0.0):
            return None
        return n / d

    def _quick_ratio(self, latest_balance: dict[str, Any]) -> float | None:
        cash = self._to_float(latest_balance.get("Cash And Cash Equivalents"))
        receivables = self._to_float(latest_balance.get("Receivables"))
        current_liabilities = self._to_float(latest_balance.get("Current Liabilities"))
        if current_liabilities in (None, 0.0):
            return None
        if cash is None and receivables is None:
            return None
        return ((cash or 0.0) + (receivables or 0.0)) / current_liabilities

    def _roic(self, income: dict[str, Any], balance: dict[str, Any], valuation: dict[str, Any]) -> float | None:
        ebit = self._to_float(income.get("Operating Income") or income.get("EBIT"))
        if ebit is None:
            return None
        total_debt = self._to_float(balance.get("Total Debt") or valuation.get("totalDebt"))
        total_equity = self._to_float(balance.get("Stockholders Equity"))
        cash = self._to_float(balance.get("Cash And Cash Equivalents") or valuation.get("totalCash"))
        invested_capital = None
        if total_equity is not None or total_debt is not None:
            invested_capital = (total_equity or 0.0) + (total_debt or 0.0) - (cash or 0.0)
        if invested_capital in (None, 0.0):
            return None
        return ebit / invested_capital

    def _net_debt(self, model: StockModel) -> float | None:
        debt = self._to_float((model.balance_sheet or {}).get("snapshot", {}).get("totalDebt") or model.valuation.get("totalDebt"))
        cash = self._to_float((model.balance_sheet or {}).get("snapshot", {}).get("totalCash") or model.valuation.get("totalCash"))
        if debt is None and cash is None:
            return None
        return (debt or 0.0) - (cash or 0.0)

    def _series_by_candidates(self, statements: list[dict[str, Any]], candidates: list[str]) -> list[tuple[str, float]]:
        series: list[tuple[str, float]] = []
        for row in statements:
            if not isinstance(row, dict):
                continue
            value = None
            for key in candidates:
                value = row.get(key)
                if value is not None:
                    break
            as_float = self._to_float(value)
            if as_float is None:
                continue
            dt = row.get("date")
            if not isinstance(dt, str):
                continue
            series.append((dt, as_float))
        series.sort(key=lambda x: x[0])
        return series

    def _eps_series(self, statements: list[dict[str, Any]]) -> list[tuple[str, float]]:
        eps: list[tuple[str, float]] = []
        for row in statements:
            if not isinstance(row, dict):
                continue
            net_income = self._to_float(row.get("Net Income"))
            shares = self._to_float(row.get("Diluted Average Shares") or row.get("Basic Average Shares"))
            date = row.get("date")
            if net_income is None or shares in (None, 0.0) or not isinstance(date, str):
                continue
            eps.append((date, net_income / shares))
        eps.sort(key=lambda x: x[0])
        return eps

    def _latest_growth(self, series: list[tuple[str, float]]) -> float | None:
        if len(series) < 2:
            return None
        prev = series[-2][1]
        last = series[-1][1]
        if prev == 0:
            return None
        return (last / prev) - 1.0

    @staticmethod
    def _last_date(series: list[tuple[str, float]]) -> str | None:
        return series[-1][0] if series else None

    def _normalize_price_history(self, history: list[dict[str, Any]]) -> list[dict[str, Any]]:
        normalized = []
        for entry in history:
            if not isinstance(entry, dict):
                continue
            date_raw = entry.get("date")
            close = self._to_float(entry.get("close"))
            if close is None or not isinstance(date_raw, str):
                continue
            normalized.append({"date": date_raw, "close": close})
        normalized.sort(key=lambda x: x["date"])
        return normalized

    @staticmethod
    def _daily_returns(closes: list[float]) -> list[float]:
        returns = []
        for idx in range(1, len(closes)):
            prev = closes[idx - 1]
            current = closes[idx]
            if prev == 0:
                continue
            returns.append((current / prev) - 1.0)
        return returns

    def _annualized_volatility(self, returns: list[float]) -> float | None:
        std = self._stddev(returns)
        if std is None:
            return None
        return std * math.sqrt(252)

    def _sharpe_ratio(self, returns: list[float], risk_free_rate: float = 0.02) -> float | None:
        if not returns:
            return None
        mean_return = sum(returns) / len(returns)
        std = self._stddev(returns)
        if std in (None, 0.0):
            return None
        daily_rf = risk_free_rate / 252
        return ((mean_return - daily_rf) / std) * math.sqrt(252)

    @staticmethod
    def _stddev(values: list[float]) -> float | None:
        if len(values) < 2:
            return None
        mean_val = sum(values) / len(values)
        variance = sum((v - mean_val) ** 2 for v in values) / (len(values) - 1)
        return math.sqrt(variance)

    def _max_drawdown(self, prices: list[dict[str, Any]]) -> float | None:
        if not prices:
            return None
        peak = prices[0]["close"]
        max_dd = 0.0
        for point in prices:
            close = point["close"]
            peak = max(peak, close)
            if peak == 0:
                continue
            drawdown = (close / peak) - 1.0
            max_dd = min(max_dd, drawdown)
        return max_dd

    def _total_return(self, prices: list[dict[str, Any]]) -> float | None:
        if len(prices) < 2:
            return None
        start = prices[0]["close"]
        end = prices[-1]["close"]
        if start == 0:
            return None
        return (end / start) - 1.0

    def _cagr(self, prices: list[dict[str, Any]]) -> float | None:
        if len(prices) < 2:
            return None
        start_dt = datetime.date.fromisoformat(prices[0]["date"])
        end_dt = datetime.date.fromisoformat(prices[-1]["date"])
        years = (end_dt - start_dt).days / 365.25
        if years <= 0:
            return None
        total_return = self._total_return(prices)
        if total_return is None or (1.0 + total_return) <= 0:
            return None
        return (1.0 + total_return) ** (1.0 / years) - 1.0

    def _returns_series(self, prices: list[dict[str, Any]]) -> list[dict[str, Any]]:
        out = []
        for idx in range(1, len(prices)):
            prev = prices[idx - 1]["close"]
            current = prices[idx]["close"]
            if prev == 0:
                continue
            out.append({"date": prices[idx]["date"], "value": (current / prev) - 1.0})
        return out

    def _drawdown_series(self, prices: list[dict[str, Any]]) -> list[dict[str, Any]]:
        out = []
        if not prices:
            return out
        peak = prices[0]["close"]
        for point in prices:
            peak = max(peak, point["close"])
            value = None if peak == 0 else (point["close"] / peak) - 1.0
            out.append({"date": point["date"], "value": value})
        return out

    def _align_series(self, series_a: list[dict[str, Any]], series_b: list[dict[str, Any]]) -> list[tuple[str, float, float]]:
        map_b = {p["date"]: p["close"] for p in series_b}
        aligned = []
        for point in series_a:
            date_key = point["date"]
            if date_key not in map_b:
                continue
            aligned.append((date_key, point["close"], map_b[date_key]))
        return aligned

    def _relative_series(self, company_prices: list[dict[str, Any]], benchmark_prices: list[dict[str, Any]]) -> list[dict[str, Any]]:
        aligned = self._align_series(company_prices, benchmark_prices)
        if len(aligned) < 2:
            return []
        c0 = aligned[0][1]
        b0 = aligned[0][2]
        if c0 == 0 or b0 == 0:
            return []
        out = []
        for date_key, c, b in aligned:
            company_norm = c / c0
            benchmark_norm = b / b0
            out.append({"date": date_key, "company_indexed": company_norm, "benchmark_indexed": benchmark_norm, "relative_spread": company_norm - benchmark_norm})
        return out

    def _series_total_return(self, values: list[float]) -> float | None:
        if len(values) < 2:
            return None
        if values[0] == 0:
            return None
        return (values[-1] / values[0]) - 1.0

    def _beta(self, company_prices: list[dict[str, Any]], benchmark_prices: list[dict[str, Any]]) -> float | None:
        aligned = self._align_series(company_prices, benchmark_prices)
        if len(aligned) < 3:
            return None
        company_returns = []
        benchmark_returns = []
        for idx in range(1, len(aligned)):
            prev = aligned[idx - 1]
            cur = aligned[idx]
            if prev[1] == 0 or prev[2] == 0:
                continue
            company_returns.append((cur[1] / prev[1]) - 1.0)
            benchmark_returns.append((cur[2] / prev[2]) - 1.0)
        if len(company_returns) < 2 or len(benchmark_returns) < 2:
            return None
        mean_c = sum(company_returns) / len(company_returns)
        mean_b = sum(benchmark_returns) / len(benchmark_returns)
        cov = sum((c - mean_c) * (b - mean_b) for c, b in zip(company_returns, benchmark_returns)) / (len(company_returns) - 1)
        var_b = sum((b - mean_b) ** 2 for b in benchmark_returns) / (len(benchmark_returns) - 1)
        if var_b == 0:
            return None
        return cov / var_b
