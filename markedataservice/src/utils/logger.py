import logging
from pathlib import Path

from finanzuebersicht_shared import configure_application_logging, get_settings

PROJECT_ROOT = Path(__file__).resolve().parents[3]
LOG_DIR = PROJECT_ROOT / "logs"
MARKETDATASERVICE_LOG = LOG_DIR / "markedataservice.log"
_LOGGING_CONFIGURED = False


def setup_logger(name: str | None = None) -> logging.Logger:
    """
    Konfiguriert und liefert einen Logger mit Konsolen- und Datei-Handler.
    """
    global _LOGGING_CONFIGURED
    if not _LOGGING_CONFIGURED:
        settings = get_settings()
        configure_application_logging(
            log_file=MARKETDATASERVICE_LOG,
            service_name="markedataservice",
            verbosity=settings.log_verbosity,
        )
        _LOGGING_CONFIGURED = True
    return logging.getLogger(name)


# Globaler Root-Logger
logger = setup_logger()
