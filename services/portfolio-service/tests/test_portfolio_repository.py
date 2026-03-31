# ruff: noqa: E402
from __future__ import annotations

import sys
from pathlib import Path
from uuid import UUID

import mongomock
import pytest

ROOT = Path(__file__).resolve().parents[3]
SHARED_SRC = ROOT / "shared" / "src"
if str(SHARED_SRC) not in sys.path:
    sys.path.insert(0, str(SHARED_SRC))

SERVICE_ROOT = Path(__file__).resolve().parents[1]
if "app" in sys.modules:
    del sys.modules["app"]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

import app.dependencies as portfolio_dependencies
from app.config import get_settings
from app.dependencies import get_mongo_client, get_mongo_database, get_repository
from app.models import Holding, Portfolio
from app.repositories import InMemoryPortfolioRepository, MongoPortfolioRepository


def test_mongo_repository_persists_across_instances() -> None:
    client = mongomock.MongoClient()
    database = client["finanzuebersicht"]
    repo_a = MongoPortfolioRepository(database, portfolio_collection="portfolios", holding_collection="holdings")

    portfolio = Portfolio(
        portfolio_id=UUID("20000000-0000-0000-0000-000000000001"),
        person_id=UUID("00000000-0000-0000-0000-000000000101"),
        display_name="Langfrist",
        created_at="2026-01-01T00:00:00+00:00",
        updated_at="2026-01-01T00:00:00+00:00",
    )
    repo_a.create_portfolio(portfolio)
    repo_a.create_holding(
        Holding(
            holding_id=UUID("30000000-0000-0000-0000-000000000001"),
            portfolio_id=portfolio.portfolio_id,
            symbol="AAPL",
            quantity=1,
            acquisition_price=100,
            currency="EUR",
            buy_date="2026-01-05",
        )
    )

    repo_b = MongoPortfolioRepository(database, portfolio_collection="portfolios", holding_collection="holdings")
    assert repo_b.get_portfolio(portfolio.portfolio_id) is not None
    assert len(repo_b.list_holdings(portfolio.portfolio_id)) == 1


@pytest.mark.parametrize(
    ("backend", "expected_type"),
    [("inmemory", InMemoryPortfolioRepository), ("mongo", MongoPortfolioRepository)],
)
def test_repository_backend_selection(
    monkeypatch: pytest.MonkeyPatch,
    backend: str,
    expected_type: type[InMemoryPortfolioRepository] | type[MongoPortfolioRepository],
) -> None:
    monkeypatch.setenv("PORTFOLIO_REPOSITORY_BACKEND", backend)
    monkeypatch.setattr(portfolio_dependencies, "MongoClient", mongomock.MongoClient)

    get_repository.cache_clear()
    get_mongo_database.cache_clear()
    get_mongo_client.cache_clear()
    get_settings.cache_clear()

    repository = get_repository()
    assert isinstance(repository, expected_type)
