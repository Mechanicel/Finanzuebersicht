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

from app.config import Settings
from app.dependencies import get_identifier_resolver
from app.identity import FmpIdentifierResolver, NoopIdentifierResolver, OpenFigiIdentifierResolver


def _reset_cache() -> None:
    get_identifier_resolver.cache_clear()


def test_get_identifier_resolver_prefers_fmp_when_configured(monkeypatch) -> None:
    settings = Settings(
        identifier_resolver="auto",
        fmp_enabled=True,
        fmp_api_key="fmp-key",
        openfigi_enabled=True,
        openfigi_api_key="openfigi-key",
    )
    monkeypatch.setattr("app.dependencies.get_settings", lambda: settings)
    _reset_cache()

    resolver = get_identifier_resolver()

    assert isinstance(resolver, FmpIdentifierResolver)


def test_get_identifier_resolver_uses_openfigi_as_legacy_fallback(monkeypatch) -> None:
    settings = Settings(
        identifier_resolver="auto",
        fmp_enabled=True,
        fmp_api_key=None,
        openfigi_enabled=True,
        openfigi_api_key="openfigi-key",
    )
    monkeypatch.setattr("app.dependencies.get_settings", lambda: settings)
    _reset_cache()

    resolver = get_identifier_resolver()

    assert isinstance(resolver, OpenFigiIdentifierResolver)


def test_get_identifier_resolver_falls_back_to_noop_without_provider(monkeypatch) -> None:
    settings = Settings(
        identifier_resolver="auto",
        fmp_enabled=False,
        openfigi_enabled=False,
    )
    monkeypatch.setattr("app.dependencies.get_settings", lambda: settings)
    _reset_cache()

    resolver = get_identifier_resolver()

    assert isinstance(resolver, NoopIdentifierResolver)
