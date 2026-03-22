# FTSEGlobalAllCap.py
import logging
import datetime
from typing import Any, Dict, List, Set

from src.models.ETFData import ETFData
from src.models.stock_model import StockModel

logger = logging.getLogger(__name__)

# Länder, die für FTSE Global All Cap ex US aufgenommen werden können (ex-USA, Developed + Emerging)
ELIGIBLE_COUNTRIES: Set[str] = {
    'Canada', 'Germany', 'France', 'Japan', 'Australia',
    'United Kingdom', 'Switzerland', 'Sweden', 'Finland', 'Denmark',
    'Netherlands', 'Norway', 'New Zealand', 'Singapore', 'Belgium',
    'Austria', 'Ireland', 'Hong Kong',
    'China', 'India', 'Brazil', 'South Africa', 'Russia', 'Mexico',
    'Taiwan', 'South Korea', 'Thailand', 'Malaysia', 'Chile', 'Colombia',
    'Peru', 'Poland', 'Czech Republic', 'Hungary'
}

# Börsen laut FTSE Ground Rules (Beispiel, bitte vollständig pflegen)
ELIGIBLE_EXCHANGES: Set[str] = {
    "London Stock Exchange", "Euronext", "Tokyo Stock Exchange",
    "Hong Kong Stock Exchange", "Shanghai Stock Exchange",
    "Shenzhen Stock Exchange", "Bursa Malaysia", "Xetra",
}

CRITERIA = {
    'ftseglobalallcap': {
        'markets': ELIGIBLE_COUNTRIES,
        'eligible_exchanges': ELIGIBLE_EXCHANGES,
        'min_free_float': 0.05,              # ≥ 5 %
        'min_investable_mcap': 150_000_000,  # ≥ 150 Mio USD
        'min_liquidity_usd': 1_000_000       # ≥ 1 Mio USD pro Tag
    }
}

def default_score(
    metrics: Dict[str, Any],
    basic: Dict[str, Any],
    cfg: Dict[str, Any]
) -> (int, int):
    """
    Zählt erfüllte Kriterien für FTSE Global All Cap ex US:
      1) Marktzugehörigkeit
      2) Free Float ≥ min_free_float
      3) Investable Market Cap ≥ min_investable_mcap
      4) Börse in eligible_exchanges
      5) Liquidität ≥ min_liquidity_usd
    Liefert (met, total=5).
    """
    met = 0
    total = 5

    country = basic.get('country')
    logger.debug("[FTSE] Prüfe Marktzugehörigkeit: Country=%s", country)
    if country in cfg['markets']:
        met += 1
        logger.debug("[FTSE] Markt-Kriterium erfüllt")
    else:
        logger.debug("[FTSE] Markt-Kriterium NICHT erfüllt")

    ff = metrics.get('freeFloat') or 0
    logger.debug("[FTSE] Prüfe Free Float: %.2f%% (min %.2f%%)", ff * 100, cfg['min_free_float'] * 100)
    if ff >= cfg['min_free_float']:
        met += 1
        logger.debug("[FTSE] Free Float-Kriterium erfüllt")
    else:
        logger.debug("[FTSE] Free Float-Kriterium NICHT erfüllt")

    mc = metrics.get('marketCap') or 0
    investable = mc * ff
    logger.debug("[FTSE] Berechne investierbare Marktkap: %.2f USD (min %.2f USD)", investable, cfg['min_investable_mcap'])
    if investable >= cfg['min_investable_mcap']:
        met += 1
        logger.debug("[FTSE] Investable Market Cap-Kriterium erfüllt")
    else:
        logger.debug("[FTSE] Investable Market Cap-Kriterium NICHT erfüllt")

    exchange = basic.get('exchange')
    logger.debug("[FTSE] Prüfe Börse: %s", exchange)
    if exchange in cfg['eligible_exchanges']:
        met += 1
        logger.debug("[FTSE] Exchange-Kriterium erfüllt")
    else:
        logger.debug("[FTSE] Exchange-Kriterium NICHT erfüllt")

    shares = metrics.get('sharesOutstanding') or 0
    price = mc / shares if shares else 0
    liquidity = (metrics.get('averageVolume') or 0) * price
    logger.debug("[FTSE] Prüfe Liquidität: %.2f USD/Tag (min %.2f USD)", liquidity, cfg['min_liquidity_usd'])
    if liquidity >= cfg['min_liquidity_usd']:
        met += 1
        logger.debug("[FTSE] Liquiditäts-Kriterium erfüllt")
    else:
        logger.debug("[FTSE] Liquiditäts-Kriterium NICHT erfüllt")

    logger.debug("[FTSE] Scoring abgeschlossen: %d von %d Kriterien erfüllt", met, total)
    return met, total

def bewerte_ftseglobalallcap(
    self,
    model: StockModel
) -> StockModel:
    """
    Bewertet FTSE Global All Cap ex US und füllt model.etf['ftseglobalallcap'] mit:
      {
        'erfüllt': '<XX>%',
        'entries': [ {date, country, exchange, marketCap, averageVolume, freeFloat}, … ]
      }
    """
    logger.debug("[FTSE] Starte Bewertung für ISIN=%s", model.isin)

    # a) Daten & Scoring
    metrics = model.metrics or self.provider.fetch_metrics(model.isin)
    basic   = model.basic
    cfg     = CRITERIA['ftseglobalallcap']
    logger.debug("[FTSE] Aktuelle Metrics: %s", metrics)
    logger.debug("[FTSE] Basisinfos: %s", basic)

    met, total = default_score(metrics, basic, cfg)
    fulfilled = f"{int(met * 100 / total)}%"
    logger.debug("[FTSE] Gesamt-Erfüllungsgrad: %s", fulfilled)

    # b) Einträge aufbauen (heute + Quartals-Historie)
    entries: List[Dict[str, Any]] = []
    today = datetime.date.today().isoformat()
    entries.append({
        'date':          today,
        'country':       basic.get('country'),
        'exchange':      basic.get('exchange'),
        'marketCap':     metrics.get('marketCap'),
        'averageVolume': metrics.get('averageVolume'),
        'freeFloat':     metrics.get('freeFloat'),
    })
    logger.debug("[FTSE] Aktueller Eintrag hinzugefügt: %s", entries[-1])

    for rec in model.metrics_history:
        entry = {
            'date':          rec['date'],
            'country':       basic.get('country'),
            'exchange':      basic.get('exchange'),
            'marketCap':     rec.get('marketCap'),
            'averageVolume': rec.get('averageVolume'),
            'freeFloat':     metrics.get('freeFloat'),
        }
        entries.append(entry)
        logger.debug("[FTSE] Historischer Eintrag hinzugefügt: %s", entry)

    # c) Sortieren & Limitieren (letzte 8 Einträge)
    entries.sort(key=lambda e: e['date'], reverse=True)
    entries = entries[:8]
    logger.debug("[FTSE] Nach Sortierung und Limitierung Einträge count=%d", len(entries))

    # d) In Modell schreiben
    model.etf['ftseglobalallcap'] = ETFData(erfüllt=fulfilled, entries=entries)
    logger.debug("[FTSE] model.etf['ftseglobalallcap'] gesetzt")
    return model
