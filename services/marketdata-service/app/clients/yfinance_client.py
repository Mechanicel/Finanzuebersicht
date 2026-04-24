from __future__ import annotations

import math
from datetime import datetime
from typing import Any

from app.models import UpstreamServiceError


ETF_FUNDS_DATA_FALLBACK: dict[str, str] = {
    "VGWL.DE": "VT",
    "EUNK.DE": "XMME.L",
}


class YFinanceClient:
    @staticmethod
    def _get_yf_module():
        try:
            import yfinance as yf
        except ImportError as exc:
            raise UpstreamServiceError("yfinance dependency is unavailable") from exc
        return yf

    def fetch_info(self, symbol: str) -> dict[str, Any]:
        """Fetch ticker.info and return a cleaned subset. Expensive (~500ms) – cache aggressively."""
        try:
            yf = self._get_yf_module()
            ticker = yf.Ticker(symbol)
            raw: dict[str, Any] = ticker.info or {}
        except Exception as exc:
            raise UpstreamServiceError("Market data provider temporarily unavailable") from exc
        return self._clean_info(raw)

    @staticmethod
    def _clean_info(raw: dict[str, Any]) -> dict[str, Any]:
        """Extract and sanitize the useful fields from ticker.info."""
        def _float(key: str) -> float | None:
            v = raw.get(key)
            if isinstance(v, (int, float)) and math.isfinite(v):
                return float(v)
            return None

        def _int(key: str) -> int | None:
            v = raw.get(key)
            if isinstance(v, (int, float)) and math.isfinite(v):
                return int(v)
            return None

        def _str(key: str) -> str | None:
            v = raw.get(key)
            return str(v).strip() if isinstance(v, str) and v.strip() else None

        def _float_pct_to_dec(key: str) -> float | None:
            # yfinance returns some fields (e.g. ytdReturn) as percent (−11.3 = −11.3 %)
            # rather than decimal (−0.113). Divide by 100 so all rates use the same convention.
            v = raw.get(key)
            if isinstance(v, (int, float)) and math.isfinite(v):
                return float(v) / 100.0
            return None

        return {
            "quote_type": _str("quoteType"),
            "financial_currency": _str("financialCurrency"),
            "currency": _str("currency"),
            "long_name": _str("longName"),
            "short_name": _str("shortName"),
            "sector": _str("sector"),
            "industry": _str("industry"),
            "long_business_summary": _str("longBusinessSummary"),
            "market_cap": _float("marketCap"),
            "enterprise_value": _float("enterpriseValue"),
            "trailing_pe": _float("trailingPE"),
            "forward_pe": _float("forwardPE"),
            "price_to_book": _float("priceToBook"),
            "dividend_yield": _float("dividendYield"),
            "trailing_annual_dividend_yield": _float("trailingAnnualDividendYield"),
            "beta": _float("beta"),
            "fifty_two_week_high": _float("fiftyTwoWeekHigh"),
            "fifty_two_week_low": _float("fiftyTwoWeekLow"),
            "average_volume": _int("averageVolume"),
            "total_cash": _float("totalCash"),
            "total_debt": _float("totalDebt"),
            "total_revenue": _float("totalRevenue"),
            "ebitda": _float("ebitda"),
            "profit_margins": _float("profitMargins"),
            "gross_margins": _float("grossMargins"),
            "operating_margins": _float("operatingMargins"),
            "return_on_assets": _float("returnOnAssets"),
            "return_on_equity": _float("returnOnEquity"),
            "earnings_per_share": _float("trailingEps"),
            "forward_eps": _float("forwardEps"),
            "book_value": _float("bookValue"),
            "revenue_growth": _float("revenueGrowth"),
            "debt_to_equity": _float("debtToEquity"),
            "current_ratio": _float("currentRatio"),
            "quick_ratio": _float("quickRatio"),
            "free_cashflow": _float("freeCashflow"),
            "operating_cashflow": _float("operatingCashflow"),
            # ETF-specific
            "total_assets": _float("totalAssets"),
            "fund_family": _str("fundFamily"),
            "fund_inception_date": _str("fundInceptionDate"),
            "legal_type": _str("legalType"),
            "yield": _float("yield"),
            "ytd_return": _float_pct_to_dec("ytdReturn"),
            "three_year_average_return": _float("threeYearAverageReturn"),
            "five_year_average_return": _float("fiveYearAverageReturn"),
        }

    def fetch_etf_data(self, symbol: str) -> dict[str, Any]:
        """Fetch ETF-specific data: top holdings, sector weights, asset classes."""
        try:
            yf = self._get_yf_module()
            ticker = yf.Ticker(symbol)
            info = ticker.info or {}
        except Exception as exc:
            raise UpstreamServiceError("Market data provider temporarily unavailable") from exc

        # Try funds_data from original symbol; fall back to US equivalent if available.
        funds = self._fetch_funds_data(ticker, symbol)
        funds_data_source: str | None = None
        if funds["has_data"]:
            funds_data_source = symbol
        else:
            fallback_symbol = ETF_FUNDS_DATA_FALLBACK.get(symbol)
            if fallback_symbol:
                try:
                    fallback_ticker = yf.Ticker(fallback_symbol)
                    fallback_funds = self._fetch_funds_data(fallback_ticker, fallback_symbol)
                    if fallback_funds["has_data"]:
                        funds = fallback_funds
                        funds_data_source = fallback_symbol
                except Exception:
                    pass

        def _float(key: str) -> float | None:
            v = info.get(key)
            if isinstance(v, (int, float)) and math.isfinite(v):
                return float(v)
            return None

        def _str(key: str) -> str | None:
            v = info.get(key)
            return str(v).strip() if isinstance(v, str) and v.strip() else None

        def _pct_to_dec(key: str) -> float | None:
            v = info.get(key)
            if isinstance(v, (int, float)) and math.isfinite(v):
                return float(v) / 100.0
            return None

        return {
            "aum": _float("totalAssets"),
            "fund_family": _str("fundFamily"),
            "inception_date": _str("fundInceptionDate"),
            "legal_type": _str("legalType"),
            "expense_ratio": _float("annualReportExpenseRatio"),
            "yield": _float("yield"),
            "ytd_return": _pct_to_dec("ytdReturn"),
            "three_year_return": _float("threeYearAverageReturn"),
            "five_year_return": _float("fiveYearAverageReturn"),
            "top_holdings": funds["top_holdings"],
            "sector_weights": funds["sector_weights"],
            "asset_classes": funds["asset_classes"],
            "equity_holdings": funds["equity_holdings"],
            "bond_holdings": funds["bond_holdings"],
            "funds_data_source": funds_data_source,
        }

    @staticmethod
    def _fetch_funds_data(ticker: Any, symbol: str) -> dict[str, Any]:
        """Extract holdings/sector data from ticker.funds_data. Returns empty collections on failure."""
        top_holdings: list[dict[str, Any]] = []
        sector_weights: dict[str, float] = {}
        asset_classes: dict[str, float] = {}
        equity_holdings: dict[str, Any] = {}
        bond_holdings: dict[str, Any] = {}

        try:
            fd = ticker.funds_data

            if fd is not None and hasattr(fd, "top_holdings") and fd.top_holdings is not None:
                df = fd.top_holdings
                for symbol_key, row in df.iterrows():
                    try:
                        holding: dict[str, Any] = {"symbol": str(symbol_key)}
                        name = row.get("Name") or row.get("name")
                        if name is not None:
                            holding["name"] = str(name)
                        pct = row.get("Holding Percent") or row.get("holdingPercent")
                        if isinstance(pct, (int, float)) and math.isfinite(pct):
                            holding["weight"] = float(pct)
                        top_holdings.append(holding)
                    except Exception:
                        continue

            if fd is not None and hasattr(fd, "sector_weightings") and fd.sector_weightings:
                for key, value in fd.sector_weightings.items():
                    if isinstance(value, (int, float)) and math.isfinite(value):
                        sector_weights[str(key)] = float(value)

            if fd is not None and hasattr(fd, "asset_classes") and fd.asset_classes:
                for key, value in fd.asset_classes.items():
                    if isinstance(value, (int, float)) and math.isfinite(value):
                        asset_classes[str(key)] = float(value)

            if fd is not None and hasattr(fd, "equity_holdings") and fd.equity_holdings is not None:
                df_eq = fd.equity_holdings
                for metric_name, row in df_eq.iterrows():
                    try:
                        fund_val = row.get(symbol, row.iloc[0] if len(row) > 0 else None)
                        if fund_val is not None:
                            try:
                                fv = float(fund_val)
                                if math.isfinite(fv):
                                    equity_holdings[str(metric_name)] = fv
                            except (TypeError, ValueError):
                                pass
                    except Exception:
                        continue

            if fd is not None and hasattr(fd, "bond_holdings") and fd.bond_holdings is not None:
                df_bond = fd.bond_holdings
                for metric_name, row in df_bond.iterrows():
                    try:
                        fund_val = row.get(symbol, row.iloc[0] if len(row) > 0 else None)
                        if fund_val is not None:
                            try:
                                fv = float(fund_val)
                                if math.isfinite(fv):
                                    bond_holdings[str(metric_name)] = fv
                            except (TypeError, ValueError):
                                pass
                    except Exception:
                        continue
        except Exception:
            pass

        return {
            "has_data": bool(top_holdings or sector_weights or asset_classes),
            "top_holdings": top_holdings,
            "sector_weights": sector_weights,
            "asset_classes": asset_classes,
            "equity_holdings": equity_holdings,
            "bond_holdings": bond_holdings,
        }

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
            # Core fields (existing)
            self._set_numeric_field(row, "totalAssets", series, ["Total Assets"])
            self._set_numeric_field(
                row,
                "cashAndCashEquivalents",
                series,
                ["Cash And Cash Equivalents"],
            )
            self._set_numeric_field(
                row,
                "cashAndShortTermInvestments",
                series,
                ["Cash Cash Equivalents And Short Term Investments"],
            )
            self._set_numeric_field(row, "shortTermDebt", series, ["Current Debt"])
            self._set_numeric_field(row, "longTermDebt", series, ["Long Term Debt"])
            self._set_numeric_field(
                row,
                "totalStockholdersEquity",
                series,
                ["Stockholders Equity", "Common Stock Equity"],
            )
            # Extended fields (new)
            self._set_numeric_field(row, "currentAssets", series, ["Current Assets"])
            self._set_numeric_field(
                row,
                "totalLiabilities",
                series,
                ["Total Liabilities Net Minority Interest"],
            )
            self._set_numeric_field(row, "currentLiabilities", series, ["Current Liabilities"])
            self._set_numeric_field(row, "totalDebtDirect", series, ["Total Debt"])
            self._set_numeric_field(row, "netDebtDirect", series, ["Net Debt"])
            self._set_numeric_field(row, "accountsReceivable", series, ["Accounts Receivable"])
            self._set_numeric_field(row, "inventory", series, ["Inventory"])
            self._set_numeric_field(row, "accountsPayable", series, ["Accounts Payable"])
            self._set_numeric_field(row, "retainedEarnings", series, ["Retained Earnings"])
            self._set_numeric_field(
                row,
                "goodwillAndIntangibles",
                series,
                ["Goodwill And Other Intangible Assets"],
            )
            self._set_numeric_field(row, "netPPE", series, ["Net PPE"])
            self._set_numeric_field(row, "workingCapital", series, ["Working Capital"])
            self._set_numeric_field(
                row,
                "minorityInterest",
                series,
                ["Minority Interest"],
            )
            self._set_numeric_field(
                row,
                "totalEquityGrossMinorityInterest",
                series,
                ["Total Equity Gross Minority Interest"],
            )
            rows.append(row)
        return rows

    def income_statement(self, symbol: str, period: str) -> list[dict[str, Any]]:
        try:
            yf = self._get_yf_module()
            ticker = yf.Ticker(symbol)
            frame = ticker.income_stmt if period == "annual" else ticker.quarterly_income_stmt
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
            # Core fields (existing)
            self._set_numeric_field(row, "revenue", series, ["Total Revenue", "Revenue", "Operating Revenue"])
            self._set_numeric_field(row, "operatingIncome", series, ["Operating Income", "EBIT"])
            self._set_numeric_field(row, "netIncome", series, ["Net Income"])
            # Extended fields (new)
            self._set_numeric_field(row, "grossProfit", series, ["Gross Profit"])
            self._set_numeric_field(row, "costOfRevenue", series, ["Cost Of Revenue", "Reconciled Cost Of Revenue"])
            self._set_numeric_field(row, "ebitda", series, ["EBITDA", "Normalized EBITDA"])
            self._set_numeric_field(row, "ebit", series, ["EBIT"])
            self._set_numeric_field(row, "interestExpense", series, ["Interest Expense", "Interest Expense Non Operating"])
            self._set_numeric_field(row, "taxProvision", series, ["Tax Provision"])
            self._set_numeric_field(row, "totalExpenses", series, ["Total Expenses"])
            self._set_numeric_field(row, "sellingGeneralAdministrative", series, ["Selling General And Administration"])
            self._set_numeric_field(row, "depreciationAmortization", series, ["Reconciled Depreciation", "Depreciation And Amortization In Income Statement"])
            self._set_numeric_field(row, "epsDiluted", series, ["Diluted EPS"])
            self._set_numeric_field(row, "pretaxIncome", series, ["Pretax Income"])
            rows.append(row)
        return rows

    def cash_flow_statement(self, symbol: str, period: str) -> list[dict[str, Any]]:
        try:
            yf = self._get_yf_module()
            ticker = yf.Ticker(symbol)
            frame = ticker.cash_flow if period == "annual" else ticker.quarterly_cash_flow
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
            # Core fields (existing)
            self._set_numeric_field(row, "operatingCashFlow", series, ["Operating Cash Flow"])
            self._set_numeric_field(row, "capitalExpenditure", series, ["Capital Expenditure"])
            operating_cf = row.get("operatingCashFlow")
            capex = row.get("capitalExpenditure")
            if isinstance(operating_cf, (int, float)) and isinstance(capex, (int, float)):
                row["freeCashFlow"] = float(operating_cf) - float(capex)
            else:
                row["freeCashFlow"] = None
            # Extended fields (new)
            self._set_numeric_field(row, "dividendsPaid", series, ["Cash Dividends Paid"])
            self._set_numeric_field(row, "shareRepurchase", series, ["Repurchase Of Capital Stock", "Common Stock Payments"])
            self._set_numeric_field(row, "issuanceOfDebt", series, ["Issuance Of Debt"])
            self._set_numeric_field(row, "repaymentOfDebt", series, ["Repayment Of Debt"])
            self._set_numeric_field(row, "changeInWorkingCapital", series, ["Change In Working Capital"])
            self._set_numeric_field(row, "depreciationAmortization", series, ["Depreciation And Amortization"])
            self._set_numeric_field(row, "investingCashFlow", series, ["Investing Cash Flow"])
            self._set_numeric_field(row, "financingCashFlow", series, ["Financing Cash Flow"])
            rows.append(row)
        return rows

    @staticmethod
    def _set_numeric_field(target: dict[str, Any], target_key: str, source: Any, source_keys: list[str]) -> None:
        for source_key in source_keys:
            try:
                value = source.get(source_key)  # type: ignore[call-arg]
            except Exception:
                value = None
            if isinstance(value, (int, float)) and math.isfinite(value):
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
