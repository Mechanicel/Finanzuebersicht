from pathlib import Path

from finanzuebersicht_shared import configure_application_logging, get_settings

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOG_DIR = PROJECT_ROOT / "logs"
FRONTEND_LOG = LOG_DIR / "frontend.log"


def configure_logging() -> None:
    """Configure frontend logging once in a central place."""
    settings = get_settings()
    configure_application_logging(
        log_file=FRONTEND_LOG,
        service_name="FrontendService",
        verbosity=settings.log_verbosity,
        performance_logging=settings.performance_logging,
    )
