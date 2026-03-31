from __future__ import annotations

import importlib
import importlib.util
import warnings
from typing import cast

_YFINANCE_TIMESTAMP_UTCNOW_MESSAGE = r".*Timestamp\.utcnow is deprecated.*"
_YFINANCE_MODULE_PATTERN = r"^yfinance(\.|$)"


def _resolve_pandas4_warning_category() -> type[Warning]:
    if importlib.util.find_spec("pandas.errors") is None:
        return FutureWarning

    pandas_errors = importlib.import_module("pandas.errors")
    category = getattr(pandas_errors, "Pandas4Warning", None)
    if isinstance(category, type) and issubclass(category, Warning):
        return cast(type[Warning], category)
    return FutureWarning


def suppress_known_yfinance_pandas4_warnings() -> None:
    """Suppress only the known yfinance pandas4 Timestamp.utcnow deprecation warning."""
    warnings.filterwarnings(
        "ignore",
        message=_YFINANCE_TIMESTAMP_UTCNOW_MESSAGE,
        category=_resolve_pandas4_warning_category(),
        module=_YFINANCE_MODULE_PATTERN,
    )
