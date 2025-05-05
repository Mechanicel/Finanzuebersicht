# stock_model.py
from dataclasses import dataclass, field, asdict, is_dataclass
from typing import Any, Dict, List

@dataclass
class StockModel:
    """
    Modell zur Abbildung von Aktien-Daten:
      - isin
      - basic: Basisinfos (inkl. country)
      - metrics: aktueller Stand (inkl. freeFloat)
      - metrics_history: historische Quartalsdaten
      - etf: Mapping von ETF-Key auf ein beliebiges Objekt oder Dict
    """
    isin: str
    basic: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    metrics_history: List[Dict[str, Any]] = field(default_factory=list)
    etf: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialisiert das gesamte Modell in JSON-kompatibles Dict.
        Baut das 'etf'-Mapping so um, dass jedes Objekt
        entweder seine to_dict() nutzt oder asdict()/__dict__.
        """
        # 1) Kopf-Felder übernehmen
        result = {
            "isin": self.isin,
            "basic": self.basic,
            "metrics": self.metrics,
            "metrics_history": self.metrics_history,
        }
        # 2) ETF-Felder aufbereiten
        serialized_etf: Dict[str, Any] = {}
        for key, data in self.etf.items():
            # Priorität 1: eigene to_dict-Methode
            if hasattr(data, "to_dict") and callable(data.to_dict):
                serialized_etf[key] = data.to_dict()
            # Priorität 2: dataclass-Objekt
            elif is_dataclass(data):
                serialized_etf[key] = asdict(data)
            # Priorität 3: normales Dict oder anderes Objekt
            elif isinstance(data, dict):
                serialized_etf[key] = data
            else:
                # Fallback: alle öffentlichen Attribute
                serialized_etf[key] = {
                    k: v for k, v in getattr(data, "__dict__", {}).items()
                    if not k.startswith("_")
                }
        result["etf"] = serialized_etf
        return result


class ModelNotFoundError(Exception):
    """Wird geworfen, wenn ein angefragtes Modell/ETF nicht existiert."""
    pass
