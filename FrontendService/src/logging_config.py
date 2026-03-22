import logging
from pathlib import Path


def configure_logging(level: int = logging.INFO) -> None:
    """Configure application logging once in a central place."""
    project_root = Path(__file__).resolve().parents[2]
    log_file = project_root / "finanzuebersicht.log"

    stream_handler = logging.StreamHandler()
    file_handler = logging.FileHandler(log_file, encoding="utf-8")

    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[stream_handler, file_handler],
        force=True,
    )
