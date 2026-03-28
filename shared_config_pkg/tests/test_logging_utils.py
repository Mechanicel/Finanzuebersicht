import logging
from pathlib import Path

from finanzuebersicht_shared.config import normalize_log_verbosity
from finanzuebersicht_shared.logging_utils import (
    THIRD_PARTY_NOISY_LOGGERS,
    configure_application_logging,
)


def test_normalize_log_verbosity_uppercase_error() -> None:
    assert normalize_log_verbosity("ERROR") == "error"


def test_normalize_log_verbosity_invalid_falls_back_to_debug() -> None:
    assert normalize_log_verbosity("foo") == "debug"


def test_debug_mode_keeps_third_party_loggers_quiet(tmp_path: Path) -> None:
    configure_application_logging(tmp_path / "debug.log", verbosity="debug")
    for logger_name in THIRD_PARTY_NOISY_LOGGERS:
        assert logging.getLogger(logger_name).level == logging.WARNING


def test_trace_mode_enables_third_party_debug(tmp_path: Path) -> None:
    configure_application_logging(tmp_path / "trace.log", verbosity="trace")
    for logger_name in THIRD_PARTY_NOISY_LOGGERS:
        assert logging.getLogger(logger_name).level == logging.DEBUG
