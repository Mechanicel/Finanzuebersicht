import logging
import sys
from pathlib import Path

from FrontendService.src.logging_config import configure_logging

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REQUIRED_FILES = [
    PROJECT_ROOT / "FrontendService" / "personen.json",
    PROJECT_ROOT / "FrontendService" / "src" / "data" / "banken.json",
    PROJECT_ROOT / "FrontendService" / "src" / "data" / "kontotypen.json",
]


def _validate_runtime_environment() -> bool:
    missing = [str(path.relative_to(PROJECT_ROOT)) for path in REQUIRED_FILES if not path.exists()]
    if missing:
        logger.error(
            "Launcher-Abbruch: erforderliche Konfigurationsdateien fehlen: %s",
            ", ".join(missing),
        )
        return False

    logger.debug("Launcher-Check: Konfigurationsdateien gefunden")
    return True


def main() -> int:
    configure_logging(logging.DEBUG)
    logger.info("Launcher-Start: Finanzübersicht wird vorbereitet")

    if not _validate_runtime_environment():
        return 2

    try:
        from FrontendService.src.FrontendSerivce import run
    except ModuleNotFoundError as exc:
        logger.error(
            "Launcher-Abbruch: fehlende Abhängigkeit '%s'. Bitte '.venv' erstellen und Abhängigkeiten installieren.",
            exc.name,
        )
        logger.debug("Launcher-Fehlerdetails", exc_info=True)
        return 3

    try:
        logger.info("Launcher: zentraler Entry-Point 'FrontendService.src.FrontendSerivce.run' wird aufgerufen")
        run()
        return 0
    except Exception:
        logger.exception("Launcher-Fehler: Initialisierung der Anwendung ist fehlgeschlagen")
        return 1


if __name__ == "__main__":
    sys.exit(main())
