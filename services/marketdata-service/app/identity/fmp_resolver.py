from __future__ import annotations

import logging

from app.identity.fmp_client import FmpClient
from app.models import IdentifierResolutionResult, InstrumentIdentity


class FmpIdentifierResolver:
    def __init__(self, client: FmpClient) -> None:
        self._logger = logging.getLogger(__name__)
        self._client = client

    def resolve(
        self,
        symbol: str,
        exchange: str | None,
        company_name: str | None,
    ) -> IdentifierResolutionResult | None:
        original_symbol = symbol.strip().upper()
        original_exchange = _clean(exchange)
        company_name_input = _clean(company_name)

        lookup_candidates = _build_lookup_candidates(original_symbol, original_exchange)

        for lookup_symbol, lookup_exchange in lookup_candidates:
            normalized_lookup_exchange = _normalize(lookup_exchange)
            normalized_company_name = _normalize(company_name_input)

            try:
                matches = self._client.search_instrument(
                    symbol=lookup_symbol,
                    exchange=lookup_exchange,
                    company_name=company_name_input,
                )
            except Exception:
                self._logger.debug("fmp client failed", exc_info=True)
                return None

            if not matches:
                continue

            ranked = sorted(
                (
                    (
                        _score_candidate(item, lookup_symbol, normalized_lookup_exchange, normalized_company_name),
                        item,
                    )
                    for item in matches
                ),
                key=lambda entry: entry[0],
                reverse=True,
            )

            top_score, top_item = ranked[0]
            if top_score <= 0:
                continue
            if len(ranked) > 1 and ranked[1][0] == top_score:
                self._logger.debug("fmp ambiguous matches dropped", extra={"symbol": lookup_symbol})
                continue

            identity = InstrumentIdentity(
                symbol=original_symbol,
                exchange=original_exchange,
                company_name=_first_string(top_item, "companyName", "name") or company_name_input,
                isin=_first_string(top_item, "isin"),
                wkn=_first_string(top_item, "wkn", "securityWkn"),
                figi=_first_string(top_item, "figi"),
                provider="fmp",
                raw={
                    "lookup_symbol": lookup_symbol,
                    "lookup_exchange": lookup_exchange,
                    "result": dict(top_item),
                },
            )
            return IdentifierResolutionResult(
                identity=identity,
                provider="fmp",
                confidence="high" if top_score >= 6 else "medium",
                raw=dict(top_item),
            )

        return None


def _build_lookup_candidates(symbol: str, exchange: str | None) -> list[tuple[str, str | None]]:
    original_symbol = symbol.strip().upper()
    original_exchange = _clean(exchange)
    base_symbol = original_symbol.split(".", 1)[0]

    candidates: list[tuple[str, str | None]] = [
        (original_symbol, original_exchange),
        (original_symbol, None),
    ]
    if base_symbol != original_symbol:
        candidates.extend([(base_symbol, original_exchange), (base_symbol, None)])

    deduped: list[tuple[str, str | None]] = []
    seen: set[tuple[str, str | None]] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        deduped.append(candidate)
    return deduped


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    if not stripped:
        return None
    return stripped


def _normalize(value: str | None) -> str | None:
    cleaned = _clean(value)
    return cleaned.lower() if cleaned else None


def _extract_string(payload: dict[str, object], key: str) -> str | None:
    value = payload.get(key)
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    return None


def _first_string(payload: dict[str, object], *keys: str) -> str | None:
    for key in keys:
        value = _extract_string(payload, key)
        if value is not None:
            return value
    return None


def _score_candidate(
    candidate: dict[str, object],
    symbol: str,
    exchange: str | None,
    company_name: str | None,
) -> int:
    score = 0
    ticker = _normalize(_first_string(candidate, "symbol", "ticker"))
    exchange_code = _normalize(_first_string(candidate, "exchangeShortName", "exchange", "exchangeCode", "exchCode"))
    name = _normalize(_first_string(candidate, "companyName", "name"))

    if ticker == symbol.lower():
        score += 4
    if exchange and exchange_code == exchange:
        score += 2
    if company_name and name:
        if name == company_name:
            score += 2
        elif company_name in name or name in company_name:
            score += 1
    if _first_string(candidate, "isin"):
        score += 1
    return score
