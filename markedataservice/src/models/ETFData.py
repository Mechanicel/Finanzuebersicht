from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

@dataclass
class ETFData:
    """
    Universelles Datenmodell für ETF-spezifische Informationen:
      - erfüllt: Erfüllungsgrad in Prozent (z.B. "75%")
      - entries: Liste beliebiger Kennzahlen-Dicts pro Periode
    """
    erfüllt: Optional[str] = None
    entries: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {}
        if self.erfüllt is not None:
            d['erfüllt'] = self.erfüllt
        d['entries'] = self.entries
        return d