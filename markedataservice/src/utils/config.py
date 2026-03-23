from __future__ import annotations

from shared_config import get_settings

settings = get_settings()

MARKETDATA_HOST = settings.marketdata_host
MARKETDATA_PORT = settings.marketdata_port
