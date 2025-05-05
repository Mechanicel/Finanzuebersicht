import logging
import datetime
from typing import Any, Dict, List

from markedataservice.src.models.ETFData import ETFData
from markedataservice.src.models.stock_model import StockModel

logger = logging.getLogger(__name__)

# Konfiguration für verschiedene ETFs
CRITERIA = {
    'msciworld': {
        # Englische Länder-Bezeichnungen aus yfinance.info['country']
        'markets': {
            'United States', 'Canada', 'Germany', 'France', 'Japan', 'Australia',
            'United Kingdom', 'Switzerland', 'Sweden', 'Finland', 'Denmark',
            'Netherlands', 'Norway', 'New Zealand', 'Singapore', 'Belgium',
            'Austria', 'Ireland', 'Hong Kong'
        },
        'min_market_cap': 2_000_000_000,
        'min_free_float': 0.15,
        'min_volume': 100_000
    },
    # Weitere ETFs können hier ergänzt werden
}


def bewerte_msciworld(self, model: StockModel) -> StockModel:
    """
    Spezifische Bewertung und Aufbau der MSCI-World-Daten.
    """
    # 1) Aktuelle Daten und Score
    metrics = model.metrics or self.provider.fetch_metrics(model.isin)
    basic = model.basic
    cfg = CRITERIA['msciworld']
    met, total = default_score(metrics, basic, cfg)
    fulfilled = f"{int(met * 100 / total)}%"

    # 2) Entries zusammenstellen (aktueller Stand + Quartale)
    entries: List[Dict[str, Any]] = []
    today = datetime.date.today().isoformat()
    entries.append({
        'date': today,
        'country': basic.get('country'),
        'marketCap': metrics.get('marketCap'),
        'averageVolume': metrics.get('averageVolume'),
        'freeFloat': metrics.get('freeFloat'),
    })

    for rec in model.metrics_history:
        entries.append({
            'date': rec['date'],
            'country': basic.get('country'),
            'marketCap': rec.get('marketCap'),
            'averageVolume': rec.get('averageVolume'),
            'freeFloat': metrics.get('freeFloat'),
        })

    # 3) Sortieren und auf die letzten 8 Quartale beschränken
    entries.sort(key=lambda e: e['date'], reverse=True)
    entries = entries[:8]

    # 4) In das Modell schreiben
    model.etf['msciworld'] = ETFData(erfüllt=fulfilled, entries=entries)
    logger.debug(f"[MSCI] erfüllt={fulfilled}, entries={len(entries)}")
    return model

def default_score(metrics: Dict[str, Any], basic: Dict[str, Any], config: Dict[str, Any]) -> (int, int):
    """
    Generische Scoring-Funktion: zählt erfüllte Kriterien in config.
    Gibt (met, total).
    """
    met = 0
    total = 4
    # 1) Markt
    if basic.get('country') in config['markets']:
        met += 1
    # 2) Marktkapitalisierung
    if (metrics.get('marketCap') or 0) >= config['min_market_cap']:
        met += 1
    # 3) Free Float
    ff = metrics.get('freeFloat') or 0
    if ff >= config['min_free_float']:
        met += 1
    # 4) Liquidität
    if (metrics.get('averageVolume') or 0) >= config['min_volume']:
        met += 1
    return met, total