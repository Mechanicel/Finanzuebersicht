from __future__ import annotations

import logging
from typing import Protocol

from app.models import IdentifierResolutionResult, InstrumentIdentity


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


