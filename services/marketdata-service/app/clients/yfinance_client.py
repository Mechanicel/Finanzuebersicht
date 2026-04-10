from __future__ import annotations

from datetime import datetime
from typing import Any

from app.models import UpstreamServiceError


class YFinanceClient:
    @staticmethod
    def _get_yf_module():
        try:
            import yfinance as yf
        except ImportError as exc:
            raise UpstreamServiceError("yfinance dependency is unavailable") from exc
        return yf

    def fetch_current_price(self, symbol: str) -> float:
        try:
            yf = self._get_yf_module()
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1d", interval="1m")
            if getattr(hist, "empty", True):
                raise UpstreamServiceError("Market data provider returned no intraday data")
            close_series = hist["Close"].dropna()
            if getattr(close_series, "empty", True):
                raise UpstreamServiceError("Market data provider returned no close prices")
            last_price = close_series.iloc[-1]
            return float(last_price)
        except UpstreamServiceError:
            raise
        except Exception as exc:
            raise UpstreamServiceError("Market data provider temporarily unavailable") from exc

    def fetch_history(self, symbol: str, *, period: str, interval: str = "1d") -> Any:
        try:
            yf = self._get_yf_module()
            ticker = yf.Ticker(symbol)
            return ticker.history(period=period, interval=interval)
        except UpstreamServiceError:
            raise
        except Exception as exc:
            raise UpstreamServiceError("Market data provider temporarily unavailable") from exc

    def balance_sheet_statement(self, *, symbol: str, period: str) -> list[dict[str, Any]]:
        try:
            yf = self._get_yf_module()
            ticker = yf.Ticker(symbol)
            frame = ticker.balance_sheet if period == "annual" else ticker.quarterly_balance_sheet
        except Exception as exc:
            raise UpstreamServiceError("Market data provider temporarily unavailable") from exc

        if getattr(frame, "empty", True):
            return []

        rows: list[dict[str, Any]] = []
        for column in getattr(frame, "columns", []):
            try:
                series = frame[column]
            except Exception:
                continue
            date_value, year = self._column_to_date_and_year(column)
            row: dict[str, Any] = {
                "symbol": symbol,
                "date": date_value,
                "calendarYear": year,
                "period": "FY" if period == "annual" else "Q",
            }
            self._set_numeric_field(row, "totalAssets", series, ["Total Assets"])
            self._set_numeric_field(
                row,
                "cashAndCashEquivalents",
                series,
                ["Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments"],
            )
            self._set_numeric_field(row, "shortTermDebt", series, ["Current Debt"])
            self._set_numeric_field(row, "longTermDebt", series, ["Long Term Debt"])
            self._set_numeric_field(
                row,
                "totalStockholdersEquity",
                series,
                ["Total Equity Gross Minority Interest", "Stockholders Equity"],
            )
            rows.append(row)
        return rows

    @staticmethod
    def _set_numeric_field(target: dict[str, Any], target_key: str, source: Any, source_keys: list[str]) -> None:
        for source_key in source_keys:
            try:
                value = source.get(source_key)  # type: ignore[call-arg]
            except Exception:
                value = None
            if isinstance(value, (int, float)):
                target[target_key] = float(value)
                return
        target[target_key] = None

    @staticmethod
    def _column_to_date_and_year(column: Any) -> tuple[str | None, str | None]:
        if isinstance(column, datetime):
            return column.date().isoformat(), str(column.year)
        if hasattr(column, "date"):
            try:
                date_value = column.date()
                if hasattr(date_value, "isoformat") and hasattr(date_value, "year"):
                    return date_value.isoformat(), str(date_value.year)
            except Exception:
                pass
        if isinstance(column, str) and len(column) >= 4:
            year = column[:4] if column[:4].isdigit() else None
            return column, year
        return None, None
