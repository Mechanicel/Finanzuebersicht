import logging
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOG_DIR = PROJECT_ROOT / "logs"
FRONTEND_LOG = LOG_DIR / "frontend.log"


def configure_logging(level: int = logging.INFO) -> None:
    """Configure frontend logging once in a central place."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    stream_handler = logging.StreamHandler()
    file_handler = logging.FileHandler(FRONTEND_LOG, encoding="utf-8")

    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[stream_handler, file_handler],
        force=True,
    )
