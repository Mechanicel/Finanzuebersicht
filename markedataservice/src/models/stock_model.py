from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List


@dataclass
class CompanyAnalysisModel:
    """Stabiles internes Analysemodell für Einzelwerte und Fonds/ETFs."""

    isin: str
    instrument: Dict[str, Any] = field(default_factory=dict)
    market: Dict[str, Any] = field(default_factory=dict)
    profile: Dict[str, Any] = field(default_factory=dict)
    valuation: Dict[str, Any] = field(default_factory=dict)
    quality: Dict[str, Any] = field(default_factory=dict)
    growth: Dict[str, Any] = field(default_factory=dict)
    balance_sheet: Dict[str, Any] = field(default_factory=dict)
    cash_flow: Dict[str, Any] = field(default_factory=dict)
    analysts: Dict[str, Any] = field(default_factory=dict)
    fund: Dict[str, Any] = field(default_factory=dict)
    timeseries: Dict[str, Any] = field(default_factory=dict)
    meta: Dict[str, Any] = field(default_factory=dict)

    # Legacy-/Kompatibilitätsfelder
    basic: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    metrics_history: List[Dict[str, Any]] = field(default_factory=list)
    price_history: List[Dict[str, Any]] = field(default_factory=list)
    etf: Dict[str, Any] = field(default_factory=dict)
    aliases: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def sync_legacy_fields(self) -> None:
        """Hält alte Felder für bestehende Endpunkte synchron."""
        if not self.basic:
            self.basic = {
                "isin": self.instrument.get("isin") or self.isin,
                "symbol": self.instrument.get("symbol"),
                "shortName": self.instrument.get("short_name"),
                "longName": self.instrument.get("long_name"),
                "sector": self.profile.get("sector"),
                "industry": self.profile.get("industry"),
                "country": self.profile.get("country"),
                "exchange": self.instrument.get("exchange"),
                "currency": self.instrument.get("currency"),
            }

        if not self.metrics:
            merged_metrics = {}
            merged_metrics.update(self.market or {})
            merged_metrics.update(self.valuation or {})
            merged_metrics.update(self.quality or {})
            merged_metrics.update(self.growth or {})
            self.metrics = merged_metrics

        if not self.price_history:
            self.price_history = list((self.timeseries or {}).get("price_history") or [])

        if not self.metrics_history:
            self.metrics_history = list((self.timeseries or {}).get("metrics_history") or [])


# Abwärtskompatibilität für bestehende Imports
StockModel = CompanyAnalysisModel


class ModelNotFoundError(Exception):
    """Wird geworfen, wenn ein angefragtes Modell/ETF nicht existiert."""

    pass
