from __future__ import annotations

from finanzuebersicht_shared import get_settings

settings = get_settings()

MARKETDATA_HOST = settings.marketdata_host
MARKETDATA_PORT = settings.marketdata_port
