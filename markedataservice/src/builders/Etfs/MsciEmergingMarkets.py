# MsciEmergingMarkets.py
import logging
import datetime
from typing import Any, Dict, List

from markedataservice.src.models.ETFData import ETFData
from markedataservice.src.models.stock_model import StockModel

logger = logging.getLogger(__name__)

# 1) Konfiguration für MSCI Emerging Markets
CRITERIA = {
    'msciemergingmarkets': {
        'markets': {
            'China', 'India', 'Brazil', 'South Africa', 'Russia', 'Mexico',
            'Taiwan', 'South Korea', 'Thailand', 'Malaysia', 'Chile', 'Colombia',
            'Peru', 'Poland', 'Czech Republic', 'Hungary'
        },
        'min_market_cap': 500_000_000,    # ab 0.5 Mrd. USD
        'min_free_float': 0.15,           # 15 %
        'min_volume': 50_000              # 50.000 Stück
    }
}

# 2) Generische Scoring-Funktion (identisch zu MsciWorld)
def default_score(
    metrics: Dict[str, Any],
    basic: Dict[str, Any],
    config: Dict[str, Any]
) -> (int, int):
    """
    Zählt erfüllte Kriterien:
      1) Marktzugehörigkeit
      2) Mindest-Marktkapitalisierung
      3) Mindest-Free-Float
      4) Mindest-Liquidität
    Liefert (met, total).
    """
    met = 0
    total = 4
    # Markt
    if basic.get('country') in config['markets']:
        met += 1
    # Marktkapitalisierung
    if (metrics.get('marketCap') or 0) >= config['min_market_cap']:
        met += 1
    # Free Float
    ff = metrics.get('freeFloat') or 0
    if ff >= config['min_free_float']:
        met += 1
    # Liquidität
    if (metrics.get('averageVolume') or 0) >= config['min_volume']:
        met += 1
    return met, total

# 3) Spezifische Bewertungsfunktion
def bewerte_msciemergingmarkets(
    self,
    model: StockModel
) -> StockModel:
    """
    Bewertet das Modell nach den Emerging-Markets-Kriterien
    und füllt model.etf['msciemergingmarkets'] mit
      {
        'erfüllt': '<XX>%',
        'entries': [ {date, country, marketCap, averageVolume, freeFloat}, … ]
      }
    """
    # a) Aktuelle Daten und Scoring
    metrics = model.metrics or self.provider.fetch_metrics(model.isin)
    basic   = model.basic
    cfg     = CRITERIA['msciemergingmarkets']
    met, total = default_score(metrics, basic, cfg)
    fulfilled = f"{int(met * 100 / total)}%"

    # b) Einträge aufbauen (heute + history)
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
    # historische Quartalsdaten
    for rec in model.metrics_history:
        entries.append({
            'date':          rec['date'],
            'country':       basic.get('country'),
            'marketCap':     rec.get('marketCap'),
            'averageVolume': rec.get('averageVolume'),
            'freeFloat':     metrics.get('freeFloat'),
        })

    # c) Sortierung & Limitierung auf 8 Einträge (2 Jahre quartalsweise)
    entries.sort(key=lambda e: e['date'], reverse=True)
    entries = entries[:8]

    # d) In Modell schreiben
    model.etf['msciemergingmarkets'] = ETFData(erfüllt=fulfilled, entries=entries)
    logger.debug(f"[MSCI EM] erfüllt={fulfilled}, entries={len(entries)}")
    return model
