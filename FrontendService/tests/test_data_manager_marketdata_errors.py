from __future__ import annotations

import types

import requests

from src.data.DataManager import DataManager


class DummyResponse:
    def __init__(self, status_code=404, text='{"error": "not found"}'):
        self.status_code = status_code
        self.text = text

    def raise_for_status(self):
        raise requests.HTTPError(response=self)


def _make_dm(base_url: str = "http://marketdata") -> DataManager:
    dm = DataManager.__new__(DataManager)
    dm.settings = types.SimpleNamespace(marketdata_base_url=base_url)
    dm._available = False
    dm.repository = None
    return dm


def test_get_price_returns_fallback_on_http_error(monkeypatch):
    dm = _make_dm()

    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: DummyResponse())

    result = dm.get_price("DE000BASF111", None)

    assert result == 0.0


def test_get_company_name_returns_isin_on_http_error(monkeypatch):
    dm = _make_dm()

    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: DummyResponse())

    result = dm.get_company_name("DE000BASF111")

    assert result == "DE000BASF111"
