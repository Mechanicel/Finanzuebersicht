from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SHARED_SRC = ROOT / "shared" / "src"
if str(SHARED_SRC) not in sys.path:
    sys.path.append(str(SHARED_SRC))

SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.append(str(SERVICE_ROOT))

from app.clients.yfinance_client import YFinanceClient


class FakeSeries:
    def __init__(self, values: list[float | None]) -> None:
        self._values = values

    def dropna(self) -> "FakeSeries":
        return FakeSeries([value for value in self._values if value is not None])

    @property
    def empty(self) -> bool:
        return len(self._values) == 0

    @property
    def iloc(self):
        return self

    def __getitem__(self, idx: int):
        return self._values[idx]


class FakeDateIndex:
    def __init__(self, value: date) -> None:
        self._value = value

    def date(self) -> date:
        return self._value


class FakeDataFrame:
    def __init__(self, close_values: list[float | None] | None = None, rows: list[tuple[str, dict]] | None = None) -> None:
        self._close_values = close_values
        self._rows = rows or []

    @property
    def empty(self) -> bool:
        if self._close_values is not None:
            return len(self._close_values) == 0
        return len(self._rows) == 0

    def __getitem__(self, key: str) -> FakeSeries:
        if key != "Close" or self._close_values is None:
            raise KeyError(key)
        return FakeSeries(self._close_values)

    def iterrows(self):
        for date_str, row in self._rows:
            yyyy, mm, dd = [int(part) for part in date_str.split("-")]
            yield FakeDateIndex(date(yyyy, mm, dd)), row


class FakeBalanceSheetFrame:
    def __init__(self, columns: list[date], values_by_column: dict[date, dict[str, float]]) -> None:
        self.columns = columns
        self._values_by_column = values_by_column

    @property
    def empty(self) -> bool:
        return len(self.columns) == 0

    def __getitem__(self, column: date):
        return self._values_by_column[column]


class FakeTicker:
    def __init__(self, symbol: str, calls: list[tuple[str, str, str]]) -> None:
        self._symbol = symbol
        self._calls = calls
        annual_date = date(2025, 12, 31)
        quarter_date = date(2025, 9, 30)
        self.balance_sheet = FakeBalanceSheetFrame(
            columns=[annual_date],
            values_by_column={
                annual_date: {
                    "Total Assets": 150.0,
                    "Cash And Cash Equivalents": 12.0,
                    "Current Debt": 4.0,
                    "Long Term Debt": 11.0,
                    "Stockholders Equity": 75.0,
                }
            },
        )
        self.quarterly_balance_sheet = FakeBalanceSheetFrame(
            columns=[quarter_date],
            values_by_column={
                quarter_date: {
                    "Total Assets": 145.0,
                    "Cash And Cash Equivalents": 10.0,
                    "Current Debt": 3.0,
                    "Long Term Debt": 10.0,
                    "Stockholders Equity": 70.0,
                }
            },
        )

    def history(self, period: str, interval: str):
        self._calls.append((self._symbol, period, interval))
        if period == "1d" and interval == "1m":
            return FakeDataFrame(close_values=[31.0, None, 31.48])
        if period == "max" and interval == "1d":
            return FakeDataFrame(rows=[("2026-04-01", {"Close": 30.4})])
        return FakeDataFrame(close_values=[])


class FakeYFinance:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str]] = []

    def Ticker(self, symbol: str) -> FakeTicker:
        return FakeTicker(symbol, self.calls)


def test_fetch_current_price_uses_1d_1m_and_returns_last_close(monkeypatch) -> None:
    fake_yf = FakeYFinance()
    monkeypatch.setattr(YFinanceClient, "_get_yf_module", staticmethod(lambda: fake_yf))
    client = YFinanceClient()

    price = client.fetch_current_price("CBK.DE")

    assert price == 31.48
    assert fake_yf.calls == [("CBK.DE", "1d", "1m")]


def test_fetch_history_uses_period_and_interval(monkeypatch) -> None:
    fake_yf = FakeYFinance()
    monkeypatch.setattr(YFinanceClient, "_get_yf_module", staticmethod(lambda: fake_yf))
    client = YFinanceClient()

    data = client.fetch_history("CBK.DE", period="max", interval="1d")

    assert data.empty is False
    assert fake_yf.calls == [("CBK.DE", "max", "1d")]


def test_balance_sheet_statement_annual_maps_rows(monkeypatch) -> None:
    fake_yf = FakeYFinance()
    monkeypatch.setattr(YFinanceClient, "_get_yf_module", staticmethod(lambda: fake_yf))
    client = YFinanceClient()

    rows = client.balance_sheet_statement(symbol="CBK.DE", period="annual")

    assert len(rows) == 1
    assert rows[0]["symbol"] == "CBK.DE"
    assert rows[0]["period"] == "FY"
    assert rows[0]["calendarYear"] == "2025"
    assert rows[0]["totalAssets"] == 150.0
    assert rows[0]["shortTermDebt"] == 4.0
    assert rows[0]["longTermDebt"] == 11.0


def test_balance_sheet_statement_quarterly_maps_rows(monkeypatch) -> None:
    fake_yf = FakeYFinance()
    monkeypatch.setattr(YFinanceClient, "_get_yf_module", staticmethod(lambda: fake_yf))
    client = YFinanceClient()

    rows = client.balance_sheet_statement(symbol="CBK.DE", period="quarterly")

    assert len(rows) == 1
    assert rows[0]["period"] == "Q"
    assert rows[0]["calendarYear"] == "2025"
