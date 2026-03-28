from __future__ import annotations

import logging
import sys
from pathlib import Path

from .config import normalize_log_verbosity

APP_LOGGER_NAMESPACES = ("src", "finanzuebersicht_shared", "__main__")
THIRD_PARTY_NOISY_LOGGERS = (
    "urllib3",
    "urllib3.connectionpool",
    "pymongo",
    "pymongo.topology",
    "matplotlib",
    "matplotlib.font_manager",
)

_LEVEL_MATRIX: dict[str, dict[str, int]] = {
    "error": {"root": logging.ERROR, "app": logging.ERROR, "third_party": logging.ERROR},
    "debug": {"root": logging.WARNING, "app": logging.DEBUG, "third_party": logging.WARNING},
    "trace": {"root": logging.DEBUG, "app": logging.DEBUG, "third_party": logging.DEBUG},
}


def configure_application_logging(
    log_file: Path,
    service_name: str | None = None,
    verbosity: str = "debug",
) -> None:
    mode = normalize_log_verbosity(verbosity)
    levels = _LEVEL_MATRIX[mode]

    log_file.parent.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(levels["root"])

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)

    root_logger.addHandler(stream_handler)
    root_logger.addHandler(file_handler)

    for logger_name in APP_LOGGER_NAMESPACES:
        app_logger = logging.getLogger(logger_name)
        app_logger.setLevel(levels["app"])
        app_logger.propagate = True

    if service_name:
        service_logger = logging.getLogger(service_name)
        service_logger.setLevel(levels["app"])
        service_logger.propagate = True

    for logger_name in THIRD_PARTY_NOISY_LOGGERS:
        noisy_logger = logging.getLogger(logger_name)
        noisy_logger.setLevel(levels["third_party"])
        noisy_logger.propagate = True
