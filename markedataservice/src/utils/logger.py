import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
LOG_DIR = PROJECT_ROOT / "logs"
MARKETDATASERVICE_LOG = LOG_DIR / "markedataservice.log"


def setup_logger(name: str | None = None, level: int = logging.DEBUG) -> logging.Logger:
    """
    Konfiguriert und liefert einen Logger mit Konsolen- und Datei-Handler.
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    logger.handlers.clear()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    file_handler = logging.FileHandler(MARKETDATASERVICE_LOG, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


# Globaler Root-Logger
logger = setup_logger()
