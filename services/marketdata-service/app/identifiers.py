from __future__ import annotations

import logging
from typing import Protocol

from app.models import IdentifierResolutionResult, InstrumentIdentity
from app.openfigi_client import OpenFigiClient


class IdentifierResolver(Protocol):
    def resolve(
        self,
        symbol: str,
        exchange: str | None,
        company_name: str | None,
    ) -> IdentifierResolutionResult | None: ...


class NoopIdentifierResolver:
    def resolve(
        self,
        symbol: str,
        exchange: str | None,
        company_name: str | None,
    ) -> IdentifierResolutionResult | None:
        return None


class OpenFigiIdentifierResolver:
    def __init__(self, client: OpenFigiClient) -> None:
        self._logger = logging.getLogger(__name__)
        self._client = client

    def resolve(
        self,
        symbol: str,
        exchange: str | None,
        company_name: str | None,
    ) -> IdentifierResolutionResult | None:
        normalized_symbol = symbol.strip().upper()
        exchange_input = _clean(exchange)
        company_name_input = _clean(company_name)
        normalized_exchange = _normalize(exchange_input)
        normalized_company_name = _normalize(company_name_input)

        self._logger.debug(
            "identifier resolver called",
            extra={"symbol": normalized_symbol, "exchange": normalized_exchange},
        )

        try:
            matches = self._client.map_instrument(
                symbol=normalized_symbol,
                exchange_code=exchange_input,
                company_name=company_name_input,
            )
        except Exception:
            self._logger.debug("openfigi client failed", exc_info=True)
            return None

        if not matches:
            self._logger.debug("openfigi no match", extra={"symbol": normalized_symbol})
            return None

        ranked = sorted(
            ((_score_candidate(item, normalized_symbol, normalized_exchange, normalized_company_name), item) for item in matches),
            key=lambda entry: entry[0],
            reverse=True,
        )

        top_score, top_item = ranked[0]
        if top_score <= 0:
            self._logger.debug("openfigi no plausible match", extra={"symbol": normalized_symbol})
            return None

        if len(ranked) > 1 and ranked[1][0] == top_score:
            self._logger.debug(
                "openfigi ambiguous matches dropped",
                extra={"symbol": normalized_symbol, "top_score": top_score},
            )
            return None

        identity = InstrumentIdentity(
            symbol=_extract_string(top_item, "ticker") or normalized_symbol,
            exchange=_extract_string(top_item, "exchCode") or exchange_input,
            company_name=_extract_string(top_item, "name") or company_name_input,
            isin=_extract_string(top_item, "isin"),
            wkn=None,
            figi=_extract_string(top_item, "figi"),
            provider="openfigi",
            raw=dict(top_item),
        )
        result = IdentifierResolutionResult(
            identity=identity,
            provider="openfigi",
            confidence="high" if top_score >= 6 else "medium",
            raw=dict(top_item),
        )
        self._logger.debug(
            "openfigi resolved unique match",
            extra={"symbol": normalized_symbol, "figi": identity.figi},
        )
        return result


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


def _score_candidate(
    candidate: dict[str, object],
    symbol: str,
    exchange: str | None,
    company_name: str | None,
) -> int:
    score = 0
    ticker = _normalize(_extract_string(candidate, "ticker"))
    exch_code = _normalize(_extract_string(candidate, "exchCode"))
    name = _normalize(_extract_string(candidate, "name"))

    if ticker == symbol.lower():
        score += 4
    if exchange and exch_code == exchange:
        score += 2
    if company_name and name:
        if name == company_name:
            score += 2
        elif company_name in name or name in company_name:
            score += 1
    if _extract_string(candidate, "figi"):
        score += 1
    return score
