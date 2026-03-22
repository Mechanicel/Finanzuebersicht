import logging


def configure_logging(level: int = logging.INFO) -> None:
    """Configure application logging once in a central place."""
    root_logger = logging.getLogger()
    if root_logger.handlers:
        return

    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
