from __future__ import annotations

import sys
from pathlib import Path

import mongomock

ROOT = Path(__file__).resolve().parents[3]
SHARED_SRC = ROOT / "shared" / "src"
if str(SHARED_SRC) not in sys.path:
    sys.path.append(str(SHARED_SRC))

SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.append(str(SERVICE_ROOT))

from app.models import InstrumentIdentity
from app.repositories import SecurityIdentityRepository


def test_upsert_normalizes_lookup_and_get_returns_identity() -> None:
    client = mongomock.MongoClient()
    repository = SecurityIdentityRepository(collection=client["finanzuebersicht"]["security_identity_test"])

    repository.upsert(
        InstrumentIdentity(
            symbol=" cbk.de ",
            exchange=" ger ",
            company_name="Commerzbank AG",
            isin=" de000cbk1001 ",
            figi=" bbg000test ",
            provider="fmp",
        )
    )

    identity = repository.get("CBK.DE", "GER")

    assert identity is not None
    assert identity.symbol == "CBK.DE"
    assert identity.exchange == "GER"
    assert identity.isin == "DE000CBK1001"
    assert identity.figi == "BBG000TEST"


def test_get_without_exchange_matches_none_exchange_entries() -> None:
    client = mongomock.MongoClient()
    repository = SecurityIdentityRepository(collection=client["finanzuebersicht"]["security_identity_test_none_exchange"])

    repository.upsert(
        InstrumentIdentity(
            symbol="URTH",
            exchange=None,
            company_name="iShares MSCI World ETF",
            isin="US4642863926",
            provider="fmp",
        )
    )

    identity = repository.get("urth", None)

    assert identity is not None
    assert identity.symbol == "URTH"
    assert identity.exchange is None
