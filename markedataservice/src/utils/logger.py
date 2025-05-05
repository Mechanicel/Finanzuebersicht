import logging
import sys

def setup_logger(name: str = None, level: int = logging.DEBUG) -> logging.Logger:
    """
    Konfiguriert und liefert einen Logger mit Konsolen-Handler.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Verhindern mehrfacher Handler
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

# Globaler Root-Logger
logger = setup_logger()