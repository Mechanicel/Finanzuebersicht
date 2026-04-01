from __future__ import annotations

import requests

from app.openfigi_client import OpenFigiClient


def test_openfigi_client_mapping_request_uses_only_documented_fields(monkeypatch) -> None:
    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self):
            return [
                {
                    "data": [
                        {
                            "ticker": "IBM",
                            "exchCode": "US",
                            "name": "INTL BUSINESS MACHINES CORP",
                            "isin": "US4592001014",
                            "figi": "BBG000BLNNH6",
                        }
                    ]
                }
            ]

    captured: dict[str, object] = {}

    def fake_post(self, url, *, headers, json, timeout):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(requests.Session, "post", fake_post)

    client = OpenFigiClient(base_url="https://api.openfigi.com/v3", api_key="secret", timeout_seconds=5.0)

    result = client.map_instrument(symbol="IBM", exchange_code="US", company_name="IBM")

    assert str(captured["url"]).endswith("/mapping")
    assert captured["json"] == [{"idType": "TICKER", "idValue": "IBM", "exchCode": "US"}]
    assert "securityDescription" not in str(captured["json"])
    assert len(result) == 1
    assert result[0]["ticker"] == "IBM"


def test_openfigi_client_returns_empty_list_for_v3_warning_response(monkeypatch) -> None:
    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self):
            return [{"warning": "No identifier found."}]

    def fake_post(self, url, *, headers, json, timeout):
        return FakeResponse()

    monkeypatch.setattr(requests.Session, "post", fake_post)

    client = OpenFigiClient(base_url="https://api.openfigi.com/v3", api_key="secret", timeout_seconds=5.0)

    result = client.map_instrument(symbol="CBK", exchange_code="US")

    assert result == []
