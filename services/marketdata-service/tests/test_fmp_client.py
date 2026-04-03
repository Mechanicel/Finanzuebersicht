from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
SHARED_SRC = ROOT / "shared" / "src"
if str(SHARED_SRC) not in sys.path:
    sys.path.append(str(SHARED_SRC))

SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.append(str(SERVICE_ROOT))

from app.clients.fmp_client import FMPClient


class DummyResponse:
    def __init__(self, payload: list[dict[str, str]]) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self):
        return self._payload


def test_fmp_client_passes_api_key_and_search_query_params() -> None:
    captured: dict[str, object] = {}

    def fake_get(url: str, *, params: dict[str, object], timeout: float):
        captured["url"] = url
        captured["params"] = params
        captured["timeout"] = timeout
        return DummyResponse([{"symbol": "CBK.DE"}])

    client = FMPClient(
        base_url="https://financialmodelingprep.com/api/v3",
        api_key="secret-key",
        timeout_seconds=5.0,
        retries=0,
        backoff_factor=0.0,
    )
    client._session = SimpleNamespace(get=fake_get)

    rows = client.search_name(query="Commerzbank", limit=7)

    assert rows == [{"symbol": "CBK.DE"}]
    assert captured["url"] == "https://financialmodelingprep.com/api/v3/search-name"
    assert captured["params"] == {"query": "Commerzbank", "limit": 7, "apikey": "secret-key"}
    assert captured["timeout"] == 5.0


def test_fmp_client_profile_uses_symbol_query_param() -> None:
    captured: dict[str, object] = {}

    def fake_get(url: str, *, params: dict[str, object], timeout: float):
        captured["url"] = url
        captured["params"] = params
        captured["timeout"] = timeout
        return DummyResponse([{"symbol": "CBK.DE", "companyName": "Commerzbank AG"}])

    client = FMPClient(
        base_url="https://financialmodelingprep.com/api/v3/",
        api_key="another-key",
        timeout_seconds=9.0,
        retries=0,
        backoff_factor=0.0,
    )
    client._session = SimpleNamespace(get=fake_get)

    rows = client.profile(symbol="CBK.DE")

    assert rows[0]["companyName"] == "Commerzbank AG"
    assert captured["url"] == "https://financialmodelingprep.com/api/v3/profile"
    assert captured["params"] == {"symbol": "CBK.DE", "apikey": "another-key"}
    assert captured["timeout"] == 9.0
