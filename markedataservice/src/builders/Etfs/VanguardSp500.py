# VanguardSp500.py
import logging
import datetime
from typing import Any, Dict, List

from src.models.ETFData import ETFData
from src.models.stock_model import StockModel
from src.builders.Etfs.MsciWorld import default_score

logger = logging.getLogger(__name__)

# 1) Konfiguration für Vanguard S&P 500 ETF (VOO)
CRITERIA = {
    'voo': {
        # S&P 500 = US Large Cap
        'markets': {'United States'},
        # Nur Unternehmen ab 10 Mrd. USD Marktkapitalisierung
        'min_market_cap': 10_000_000_000,
        # Mindestens 15 % Free Float
        'min_free_float': 0.15,
        # Mindestens 200 000 Stück Tagesvolumen
        'min_volume': 200_000
    }
}

def bewerte_voo(self, model: StockModel) -> StockModel:
    """
    Bewertet das Modell nach den VOO-Kriterien
    und füllt model.etf['voo'] mit:
      {
        'erfüllt': '<XX>%',
        'entries': [ {date, country, marketCap, averageVolume, freeFloat}, … ]
      }
    """
    # a) Aktuelle Daten & Score
    metrics = model.metrics or self.provider.fetch_metrics(model.isin)
    basic   = model.basic
    cfg     = CRITERIA['voo']
    met, total = default_score(metrics, basic, cfg)
    fulfilled = f"{int(met * 100 / total)}%"

    # b) Entries aufbauen (heute + history)
    entries: List[Dict[str, Any]] = []
    today = datetime.date.today().isoformat()
    # aktueller Stand
    entries.append({
        'date':          today,
        'country':       basic.get('country'),
        'marketCap':     metrics.get('marketCap'),
        'averageVolume': metrics.get('averageVolume'),
        'freeFloat':     metrics.get('freeFloat'),
    })
    # historische Quartalsdaten (load_history vorausgesetzt aufgerufen)
    for rec in model.metrics_history:
        entries.append({
            'date':          rec['date'],
            'country':       basic.get('country'),
            'marketCap':     rec.get('marketCap'),
            'averageVolume': rec.get('averageVolume'),
            'freeFloat':     metrics.get('freeFloat'),
        })

    # c) Sortieren & Limitieren (letzte 8 Quartale = 2 Jahre)
    entries.sort(key=lambda e: e['date'], reverse=True)
    entries = entries[:8]

    # d) In Modell schreiben
    model.etf['voo'] = ETFData(erfüllt=fulfilled, entries=entries)
    logger.debug(f"[VOO] erfüllt={fulfilled}, entries={len(entries)}")
    return model
