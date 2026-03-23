from __future__ import annotations

import os
from pathlib import Path

from shared_config import get_settings

settings = get_settings()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("STOCK_DATA_DIR", str(BASE_DIR / "data" / "stocks")))
MARKETDATA_HOST = settings.marketdata_host
MARKETDATA_PORT = settings.marketdata_port
