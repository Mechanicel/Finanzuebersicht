from __future__ import annotations

import logging
import re
from datetime import UTC, date, datetime, timedelta
from statistics import pstdev
from typing import Any, Protocol
from urllib.parse import quote as urlencode

import requests
import yfinance as yf
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.models import (
    BenchmarkOption,
    DataInterval,
    DataRange,
    FundamentalsBlock,
    InstrumentDataBlocksResponse,
    InstrumentFullResponse,
    InstrumentSearchItem,
    InstrumentSelectionDetailsResponse,
    InstrumentSummary,
    MetricsBlock,
    PricePoint,
    RiskBlock,
    SnapshotBlock,
    UpstreamServiceError,
)


class MarketDataProvider(Protocol):
    def get_instrument_summary(self, symbol: str) -> InstrumentSummary | None: ...

    def get_price_series(
        self, symbol: str, data_range: DataRange, interval: DataInterval
    ) -> list[PricePoint] | None: ...

    def get_instrument_blocks(self, symbol: str) -> InstrumentDataBlocksResponse | None: ...

    def get_instrument_full(self, symbol: str) -> InstrumentFullResponse | None: ...

    def get_instrument_selection_details(self, symbol: str) -> InstrumentSelectionDetailsResponse | None: ...
    def get_instrument_hydration_payload(self, symbol: str) -> dict[str, object] | None: ...

    def search_instruments(self, query: str, limit: int) -> list[InstrumentSearchItem]: ...

    def list_benchmark_options(self) -> list[BenchmarkOption]: ...
