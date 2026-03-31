from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SHARED_SRC = ROOT / "shared" / "src"
if str(SHARED_SRC) not in sys.path:
    sys.path.append(str(SHARED_SRC))

SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.append(str(SERVICE_ROOT))

from app import warning_filters


class _FakePandas4Warning(FutureWarning):
    pass


def test_warning_filter_uses_pandas4warning_when_available(monkeypatch) -> None:
    captured: dict[str, object] = {}

    monkeypatch.setattr("app.warning_filters.importlib.util.find_spec", lambda _: object())
    monkeypatch.setattr(
        "app.warning_filters.importlib.import_module",
        lambda _: type("FakeErrors", (), {"Pandas4Warning": _FakePandas4Warning}),
    )

    def _capture(action, *, message, category, module, lineno=0, append=False):
        captured.update(
            {
                "action": action,
                "message": message,
                "category": category,
                "module": module,
                "lineno": lineno,
                "append": append,
            }
        )

    monkeypatch.setattr("app.warning_filters.warnings.filterwarnings", _capture)

    warning_filters.suppress_known_yfinance_pandas4_warnings()

    assert captured["action"] == "ignore"
    assert captured["category"] is _FakePandas4Warning
    assert captured["module"] == r"^yfinance(\.|$)"
    assert "Timestamp\\.utcnow is deprecated" in str(captured["message"])


def test_warning_filter_falls_back_to_futurewarning(monkeypatch) -> None:
    monkeypatch.setattr("app.warning_filters.importlib.util.find_spec", lambda _: None)

    assert warning_filters._resolve_pandas4_warning_category() is FutureWarning
