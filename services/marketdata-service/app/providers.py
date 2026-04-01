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


class YFinanceMarketDataProvider:
    _ISIN_RE = re.compile(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$")
    _RANGE_MAP: dict[DataRange, str] = {
        DataRange.ONE_MONTH: "1mo",
        DataRange.THREE_MONTHS: "3mo",
        DataRange.SIX_MONTHS: "6mo",
        DataRange.ONE_YEAR: "1y",
        DataRange.THREE_YEARS: "3y",
        DataRange.FIVE_YEARS: "5y",
    }
    _INTERVAL_MAP: dict[DataInterval, str] = {
        DataInterval.ONE_DAY: "1d",
        DataInterval.ONE_WEEK: "1wk",
        DataInterval.ONE_MONTH: "1mo",
    }
    _SEARCH_PROVIDER_NAME = "yfinance"

    def __init__(
        self,
        *,
        timeout_seconds: float,
        retries: int = 2,
        backoff_factor: float = 0.3,
        benchmark_options: list[BenchmarkOption] | None = None,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self._session = self._build_session(retries=retries, backoff_factor=backoff_factor)
        self._benchmarks = benchmark_options or [
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

    def get_instrument_summary(self, symbol: str) -> InstrumentSummary | None:
        ticker = self._get_ticker(symbol)
        info = self._safe_info(ticker)
        if not self._seems_known_instrument(symbol, info):
            return None
        return self._map_summary(symbol=symbol, ticker=ticker, info=info)

    def get_price_series(
        self, symbol: str, data_range: DataRange, interval: DataInterval
    ) -> list[PricePoint] | None:
        ticker = self._get_ticker(symbol)
        info = self._safe_info(ticker)
        if not self._seems_known_instrument(symbol, info):
            return None

        history = self._safe_history(
            ticker,
            period=self._RANGE_MAP[data_range],
            interval=self._INTERVAL_MAP[interval],
        )
        return self._map_price_points(history=history)

    def get_instrument_blocks(self, symbol: str) -> InstrumentDataBlocksResponse | None:
        ticker = self._get_ticker(symbol)
        info = self._safe_info(ticker)
        if not self._seems_known_instrument(symbol, info):
            return None

        history_1y = self._safe_history(ticker, period="1y", interval="1d")
        snapshot = self._build_snapshot(ticker=ticker, info=info, history_1y=history_1y)
        return InstrumentDataBlocksResponse(
            symbol=symbol,
            snapshot=snapshot,
            fundamentals=self._build_fundamentals(info),
            metrics=self._build_metrics(history_1y),
            risk=self._build_risk(info=info, history_1y=history_1y),
        )

    def get_instrument_full(self, symbol: str) -> InstrumentFullResponse | None:
        ticker = self._get_ticker(symbol)
        info = self._safe_info(ticker)
        if not self._seems_known_instrument(symbol, info):
            return None

        history_1y = self._safe_history(ticker, period="1y", interval="1d")
        return InstrumentFullResponse(
            summary=self._map_summary(symbol=symbol, ticker=ticker, info=info),
            snapshot=self._build_snapshot(ticker=ticker, info=info, history_1y=history_1y),
            fundamentals=self._build_fundamentals(info),
            metrics=self._build_metrics(history_1y),
            risk=self._build_risk(info=info, history_1y=history_1y),
        )

    def get_instrument_selection_details(self, symbol: str) -> InstrumentSelectionDetailsResponse | None:
        ticker = self._get_ticker(symbol)
        info = self._safe_info(ticker)
        if not self._seems_known_instrument(symbol, info):
            return None

        history_1y = self._safe_history(ticker, period="1y", interval="1d")
        snapshot = self._build_snapshot(ticker=ticker, info=info, history_1y=history_1y)
        summary = self._map_summary(symbol=symbol, ticker=ticker, info=info)
        return InstrumentSelectionDetailsResponse(
            symbol=summary.symbol,
            isin=summary.isin,
            wkn=summary.wkn,
            company_name=summary.company_name,
            display_name=summary.display_name,
            exchange=summary.exchange,
            currency=summary.currency,
            quote_type=summary.quote_type,
            asset_type=summary.asset_type,
            last_price=snapshot.last_price,
            change_1d_pct=snapshot.change_1d_pct,
            volume=snapshot.volume,
            as_of=datetime.now(UTC),
        )

    def get_instrument_hydration_payload(self, symbol: str) -> dict[str, object] | None:
        ticker = self._get_ticker(symbol)
        info = self._safe_info(ticker)
        if not self._seems_known_instrument(symbol, info):
            return None

        history_1y = self._safe_history_fallback(ticker, period="1y", interval="1d")
        summary = self._map_summary(symbol=symbol, ticker=ticker, info=info)
        snapshot = self._build_snapshot(ticker=ticker, info=info, history_1y=history_1y)
        fundamentals = self._build_fundamentals(info)
        metrics = self._build_metrics(history_1y)
        risk = self._build_risk(info=info, history_1y=history_1y)
        fast_info = self._safe_fast_info(ticker)

        return {
            "identity": {
                "symbol": summary.symbol,
                "isin": summary.isin,
                "wkn": summary.wkn,
                "company_name": summary.company_name,
                "display_name": summary.display_name,
                "exchange": summary.exchange,
                "currency": summary.currency,
                "quote_type": summary.quote_type,
                "asset_type": summary.asset_type,
            },
            "summary": summary.model_dump(mode="json"),
            "snapshot": snapshot.model_dump(mode="json"),
            "fundamentals": fundamentals.model_dump(mode="json"),
            "metrics": metrics.model_dump(mode="json"),
            "risk": risk.model_dump(mode="json"),
            "provider_raw": {
                "info": info,
                "fast_info": fast_info,
            },
        }

    def search_instruments(self, query: str, limit: int) -> list[InstrumentSearchItem]:
        logger = logging.getLogger(__name__)
        max_results = min(max(limit * 3, 10), 40)

        try:
            search = yf.Search(
                query=query,
                max_results=max_results,
                timeout=self.timeout_seconds,
            )
            raw_quotes = list(search.quotes or [])
        except Exception as exc:  # pragma: no cover - library/network behaviour
            logger.error(
                "marketdata search failed",
                extra={
                    "provider": self._SEARCH_PROVIDER_NAME,
                    "query": query,
                    "exception_type": type(exc).__name__,
                    "error_message": str(exc)[:240],
                },
                exc_info=True,
            )
            if self._is_upstream_search_failure(exc):
                raise UpstreamServiceError() from exc
            return []

        terms = query.strip()
        lowered = terms.lower()
        normalized_isin = terms.upper()
        exact_wkn = terms.upper() if len(terms) in {6, 7} and terms.isalnum() else None

        scored: list[tuple[int, InstrumentSearchItem]] = []
        for quote in raw_quotes:
            symbol = str(quote.get("symbol") or "").upper()
            if not symbol:
                continue
            name = str(quote.get("longname") or quote.get("shortname") or quote.get("name") or symbol)
            isin = self._normalize_optional_identifier(quote.get("isin"))

            item = InstrumentSearchItem(
                symbol=symbol,
                company_name=name,
                display_name=str(quote.get("shortname") or quote.get("longname") or name),
                isin=isin,
                wkn=None,
                exchange=quote.get("exchDisp") or quote.get("exchange"),
                currency=quote.get("currency"),
                quote_type=quote.get("quoteType"),
                asset_type=quote.get("typeDisp") or quote.get("quoteType"),
                last_price=self._to_float(quote.get("regularMarketPrice")),
                country=quote.get("region"),
                sector=None,
            )
            score = self._score_search_item(
                item=item,
                lowered_query=lowered,
                query_isin=normalized_isin,
                exact_wkn=exact_wkn,
            )
            if score > 0:
                scored.append((score, item))

        scored.sort(key=lambda pair: (pair[0], pair[1].symbol), reverse=True)
        return [item for _, item in scored[:limit]]

    @staticmethod
    def _is_upstream_search_failure(exc: Exception) -> bool:
        return isinstance(exc, requests.RequestException)

    def list_benchmark_options(self) -> list[BenchmarkOption]:
        return list(self._benchmarks)

    def _get_ticker(self, symbol: str):
        return yf.Ticker(symbol)

    @staticmethod
    def _build_session(*, retries: int, backoff_factor: float) -> requests.Session:
        retry = Retry(
            total=max(0, retries),
            backoff_factor=max(0.0, backoff_factor),
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"GET"}),
        )
        adapter = HTTPAdapter(max_retries=retry)
        session = requests.Session()
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def _safe_info(self, ticker) -> dict[str, Any]:
        try:
            return dict(ticker.info or {})
        except Exception as exc:  # pragma: no cover - library/network behaviour
            raise UpstreamServiceError() from exc

    def _safe_history(self, ticker, *, period: str, interval: str):
        try:
            return ticker.history(period=period, interval=interval, timeout=self.timeout_seconds)
        except Exception as exc:  # pragma: no cover - library/network behaviour
            raise UpstreamServiceError() from exc

    def _safe_history_fallback(self, ticker, *, period: str, interval: str):
        try:
            return self._safe_history(ticker, period=period, interval=interval)
        except UpstreamServiceError:
            return None

    @staticmethod
    def _seems_known_instrument(symbol: str, info: dict[str, Any]) -> bool:
        if not info:
            return False
        info_symbol = str(info.get("symbol") or "").upper()
        short_name = str(info.get("shortName") or info.get("longName") or "")
        return info_symbol == symbol.upper() or bool(short_name)

    def _map_summary(self, *, symbol: str, ticker, info: dict[str, Any]) -> InstrumentSummary:
        return InstrumentSummary(
            symbol=str(info.get("symbol") or symbol).upper(),
            isin=self._safe_isin(ticker, symbol=symbol, info=info),
            company_name=str(info.get("longName") or info.get("shortName") or symbol),
            display_name=info.get("shortName") or info.get("displayName"),
            wkn=None,
            exchange=str(info.get("exchange") or info.get("fullExchangeName") or "UNKNOWN"),
            currency=str(info.get("currency") or "UNKNOWN"),
            quote_type=info.get("quoteType"),
            asset_type=info.get("typeDisp") or info.get("quoteType"),
            country=info.get("country"),
            sector=info.get("sector"),
            industry=info.get("industry"),
        )

    def _safe_isin(self, ticker, *, symbol: str, info: dict[str, Any]) -> str | None:
        try:
            isin = ticker.isin
        except Exception:
            isin = None
        normalized = self._normalize_optional_identifier(isin)
        if self._is_valid_isin(normalized):
            return normalized
        return self._resolve_isin_via_businessinsider(symbol=symbol, info=info)

    @classmethod
    def _is_valid_isin(cls, value: str | None) -> bool:
        if value is None:
            return False
        return bool(cls._ISIN_RE.fullmatch(value.strip().upper()))

    @staticmethod
    def _normalize_name_for_query(value: str | None) -> str | None:
        if value is None:
            return None
        normalized = " ".join(str(value).split()).strip()
        return normalized or None

    def _build_isin_query_candidates(self, *, symbol: str, info: dict[str, Any]) -> list[str]:
        base_symbol = symbol.split(".", 1)[0].strip().upper()
        candidates = [
            self._normalize_name_for_query(info.get("shortName")),
            self._normalize_name_for_query(info.get("longName")),
            self._normalize_name_for_query(info.get("displayName")),
            symbol.strip().upper(),
            base_symbol,
        ]
        result: list[str] = []
        seen: set[str] = set()
        for candidate in candidates:
            if not candidate:
                continue
            key = candidate.upper()
            if key in seen:
                continue
            seen.add(key)
            result.append(candidate)
        return result

    def _extract_isin_from_businessinsider_payload(
        self,
        payload: str,
        *,
        expected_symbols: list[str],
    ) -> str | None:
        if not payload:
            return None

        for expected_symbol in expected_symbols:
            marker = f'"{expected_symbol.upper()}|'
            marker_index = payload.find(marker)
            if marker_index == -1:
                continue
            start = marker_index + len(marker)
            end = payload.find('"', start)
            if end == -1:
                continue
            segment = payload[start:end]
            first_field = segment.split("|", 1)[0].strip().upper()
            if self._is_valid_isin(first_field):
                return first_field

        expected_symbol_set = {symbol.upper() for symbol in expected_symbols}
        for segment in payload.split('"'):
            if "|" not in segment:
                continue
            parts = segment.split("|")
            if not parts:
                continue
            if parts[0].strip().upper() not in expected_symbol_set:
                continue
            for value in parts[1:]:
                normalized = value.strip().upper()
                if self._is_valid_isin(normalized):
                    return normalized
        return None

    def _resolve_isin_via_businessinsider(self, *, symbol: str, info: dict[str, Any]) -> str | None:
        expected_symbols = [
            symbol.upper(),
            symbol.split(".", 1)[0].upper(),
        ]
        queries = self._build_isin_query_candidates(symbol=symbol, info=info)
        for query in queries:
            url = (
                "https://markets.businessinsider.com/ajax/SearchController_Suggest"
                f"?max_results=25&query={urlencode(query)}"
            )
            try:
                response = self._session.get(url, timeout=self.timeout_seconds)
            except Exception:
                continue
            if not response.ok:
                continue
            payload = response.text
            resolved = self._extract_isin_from_businessinsider_payload(
                payload,
                expected_symbols=expected_symbols,
            )
            if resolved is not None:
                return resolved
        return None

    @staticmethod
    def _normalize_optional_identifier(value: Any) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip().upper()
        return normalized or None

    @staticmethod
    def _to_float(value: Any) -> float | None:
        try:
            return None if value is None else float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _to_int(value: Any) -> int | None:
        try:
            return None if value is None else int(value)
        except (TypeError, ValueError):
            return None

    def _build_snapshot(self, *, ticker, info: dict[str, Any], history_1y) -> SnapshotBlock:
        fast_info = self._safe_fast_info(ticker)
        last_price = (
            self._to_float(fast_info.get("lastPrice"))
            or self._to_float(info.get("currentPrice"))
            or self._last_close(history_1y)
            or 0.0
        )
        previous_close = (
            self._to_float(fast_info.get("previousClose"))
            or self._to_float(info.get("previousClose"))
            or self._to_float(info.get("regularMarketPreviousClose"))
        )
        change_1d_pct = 0.0
        if previous_close and previous_close > 0:
            change_1d_pct = ((last_price - previous_close) / previous_close) * 100

        volume = (
            self._to_int(fast_info.get("lastVolume"))
            or self._to_int(info.get("volume"))
            or self._latest_volume(history_1y)
            or 0
        )
        return SnapshotBlock(last_price=last_price, change_1d_pct=change_1d_pct, volume=volume)

    def _safe_fast_info(self, ticker) -> dict[str, Any]:
        try:
            return dict(ticker.fast_info or {})
        except Exception:
            return {}

    def _build_fundamentals(self, info: dict[str, Any]) -> FundamentalsBlock:
        return FundamentalsBlock(
            market_cap=self._to_float(info.get("marketCap")),
            pe_ratio=self._to_float(info.get("trailingPE")),
            dividend_yield=self._to_float(info.get("dividendYield")),
            revenue_growth_yoy=self._to_float(info.get("revenueGrowth")),
        )

    def _build_metrics(self, history_1y) -> MetricsBlock:
        closes = self._history_close_values(history_1y)
        if not closes:
            return MetricsBlock()

        sma_50 = sum(closes[-50:]) / min(50, len(closes))
        sma_200 = sum(closes[-200:]) / min(200, len(closes))
        rsi_14 = self._rsi(closes, window=14)
        return MetricsBlock(sma_50=sma_50, sma_200=sma_200, rsi_14=rsi_14)

    def _build_risk(self, *, info: dict[str, Any], history_1y) -> RiskBlock:
        closes = self._history_close_values(history_1y)
        daily_returns = self._daily_returns(closes)
        volatility_30d = None
        value_at_risk_95_1d = None
        if len(daily_returns) >= 2:
            window = daily_returns[-30:]
            volatility_30d = pstdev(window) * (252**0.5) if len(window) > 1 else 0.0
            sorted_returns = sorted(window)
            idx = max(0, int(0.05 * (len(sorted_returns) - 1)))
            value_at_risk_95_1d = sorted_returns[idx]

        max_drawdown_1y = self._max_drawdown(closes)

        return RiskBlock(
            beta=self._to_float(info.get("beta")),
            volatility_30d=volatility_30d,
            max_drawdown_1y=max_drawdown_1y,
            value_at_risk_95_1d=value_at_risk_95_1d,
        )

    @staticmethod
    def _daily_returns(closes: list[float]) -> list[float]:
        if len(closes) < 2:
            return []
        values: list[float] = []
        for prev, curr in zip(closes[:-1], closes[1:], strict=False):
            if prev != 0:
                values.append((curr - prev) / prev)
        return values

    @staticmethod
    def _rsi(closes: list[float], *, window: int) -> float | None:
        if len(closes) < window + 1:
            return None

        deltas = [curr - prev for prev, curr in zip(closes[:-1], closes[1:], strict=False)]
        gains = [max(delta, 0.0) for delta in deltas[-window:]]
        losses = [abs(min(delta, 0.0)) for delta in deltas[-window:]]
        avg_gain = sum(gains) / window
        avg_loss = sum(losses) / window
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    @staticmethod
    def _max_drawdown(closes: list[float]) -> float | None:
        if not closes:
            return None
        peak = closes[0]
        max_dd = 0.0
        for close in closes:
            peak = max(peak, close)
            if peak > 0:
                drawdown = (close - peak) / peak
                max_dd = min(max_dd, drawdown)
        return max_dd

    @staticmethod
    def _history_close_values(history) -> list[float]:
        if history is None or getattr(history, "empty", True):
            return []
        closes = history["Close"].dropna().tolist()
        return [float(value) for value in closes]

    @staticmethod
    def _last_close(history) -> float | None:
        closes = YFinanceMarketDataProvider._history_close_values(history)
        return closes[-1] if closes else None

    @staticmethod
    def _latest_volume(history) -> int | None:
        if history is None or getattr(history, "empty", True):
            return None
        volumes = history["Volume"].dropna().tolist()
        if not volumes:
            return None
        return int(volumes[-1])

    @staticmethod
    def _map_price_points(*, history) -> list[PricePoint]:
        if history is None or getattr(history, "empty", True):
            return []

        points: list[PricePoint] = []
        for index, row in history.iterrows():
            close_raw = row.get("Close")
            if close_raw is None:
                continue
            try:
                close = float(close_raw)
            except (TypeError, ValueError):
                continue
            if close < 0:
                continue

            if isinstance(index, datetime):
                point_date = index.date()
            elif hasattr(index, "to_pydatetime"):
                point_date = index.to_pydatetime().date()
            else:
                point_date = index if isinstance(index, date) else datetime.fromisoformat(str(index)).date()

            points.append(PricePoint(date=point_date, close=close))
        return points

    @staticmethod
    def _score_search_item(
        *,
        item: InstrumentSearchItem,
        lowered_query: str,
        query_isin: str,
        exact_wkn: str | None,
    ) -> int:
        score = 0
        symbol = item.symbol.upper()
        company = item.company_name.lower()
        display = (item.display_name or "").lower()
        isin = (item.isin or "").upper()
        wkn = (item.wkn or "").upper()

        if symbol == lowered_query.upper():
            score += 100
        elif symbol.startswith(lowered_query.upper()):
            score += 80
        elif lowered_query in symbol.lower():
            score += 45

        if isin and isin == query_isin:
            score += 110
        elif isin and query_isin in isin:
            score += 60

        if exact_wkn and wkn == exact_wkn:
            score += 90
        elif exact_wkn and wkn and exact_wkn in wkn:
            score += 40

        if company == lowered_query or display == lowered_query:
            score += 70
        elif lowered_query in company or lowered_query in display:
            score += 30

        return score


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
            "^GSPC": {
                "summary": InstrumentSummary(
                    symbol="^GSPC",
                    company_name="S&P 500 Index",
                    display_name="S&P 500",
                    exchange="SNP",
                    currency="USD",
                    quote_type="index",
                    asset_type="index",
                    country="US",
                    sector="Index",
                    industry="Broad Market",
                ),
                "base_price": 5100.0,
                "snapshot": SnapshotBlock(last_price=5120.0, change_1d_pct=0.2, volume=0),
                "fundamentals": FundamentalsBlock(),
                "metrics": MetricsBlock(sma_50=5080.0, sma_200=4920.0, rsi_14=54.0),
                "risk": RiskBlock(beta=1.0, volatility_30d=0.12, max_drawdown_1y=-0.09, value_at_risk_95_1d=-0.013),
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

    def get_instrument_selection_details(self, symbol: str) -> InstrumentSelectionDetailsResponse | None:
        key = symbol.upper()
        instrument = self._instruments.get(key)
        if instrument is None:
            return None
        summary = instrument["summary"]
        snapshot = instrument["snapshot"]
        return InstrumentSelectionDetailsResponse(
            symbol=summary.symbol,
            isin=summary.isin,
            wkn=summary.wkn,
            company_name=summary.company_name,
            display_name=summary.display_name,
            exchange=summary.exchange,
            currency=summary.currency,
            quote_type=summary.quote_type,
            asset_type=summary.asset_type,
            last_price=snapshot.last_price,
            change_1d_pct=snapshot.change_1d_pct,
            volume=snapshot.volume,
            as_of=datetime.now(UTC),
        )

    def get_instrument_hydration_payload(self, symbol: str) -> dict[str, object] | None:
        full = self.get_instrument_full(symbol)
        if full is None:
            return None
        return {
            "identity": {
                "symbol": full.summary.symbol,
                "isin": full.summary.isin,
                "wkn": full.summary.wkn,
                "company_name": full.summary.company_name,
                "display_name": full.summary.display_name,
                "exchange": full.summary.exchange,
                "currency": full.summary.currency,
                "quote_type": full.summary.quote_type,
                "asset_type": full.summary.asset_type,
            },
            "summary": full.summary.model_dump(mode="json"),
            "snapshot": full.snapshot.model_dump(mode="json"),
            "fundamentals": full.fundamentals.model_dump(mode="json"),
            "metrics": full.metrics.model_dump(mode="json"),
            "risk": full.risk.model_dump(mode="json"),
            "provider_raw": {"source": "inmemory"},
        }

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
        start = today - timedelta(days=trading_days)
        return [
            PricePoint(
                date=start + timedelta(days=idx * step_days),
                close=round(base * (1 + 0.0015 * idx), 2),
            )
            for idx in range(points)
        ]
