# ruff: noqa: E402
from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from uuid import UUID

ROOT = Path(__file__).resolve().parents[3]
SHARED_SRC = ROOT / "shared" / "src"
if str(SHARED_SRC) not in sys.path:
    sys.path.insert(0, str(SHARED_SRC))

SERVICE_ROOT = Path(__file__).resolve().parents[1]

for module_name in list(sys.modules):
    if module_name == "app" or module_name.startswith("app."):
        del sys.modules[module_name]

while str(SERVICE_ROOT) in sys.path:
    sys.path.remove(str(SERVICE_ROOT))
sys.path.insert(0, str(SERVICE_ROOT))

from app.models import AccountReadModel, PortfolioReadModel
from app.service import GatewayService

PERSON_ID = UUID("00000000-0000-0000-0000-000000000101")
ACCOUNT_1 = UUID("10000000-0000-0000-0000-000000000001")
ACCOUNT_2 = UUID("10000000-0000-0000-0000-000000000002")
PORTFOLIO_1 = UUID("20000000-0000-0000-0000-000000000001")
PORTFOLIO_2 = UUID("20000000-0000-0000-0000-000000000002")


class BindingGatewayService(GatewayService):
    def __init__(self, accounts: dict[UUID, dict]) -> None:
        self.accounts = accounts
        self.created_portfolios: list[dict] = []
        self.updated_accounts: list[tuple[UUID, UUID, UUID]] = []

    async def get_account(self, person_id: UUID, account_id: UUID) -> AccountReadModel:
        return AccountReadModel.model_validate(self.accounts[account_id])

    async def create_portfolio(self, person_id: UUID, payload) -> PortfolioReadModel:
        portfolio = {
            "portfolio_id": str(PORTFOLIO_2),
            "person_id": str(person_id),
            "display_name": payload.display_name,
            "created_at": "2026-03-01T00:00:00+00:00",
            "updated_at": "2026-03-01T00:00:00+00:00",
        }
        self.created_portfolios.append(portfolio)
        return PortfolioReadModel.model_validate(portfolio)

    async def update_account(self, person_id: UUID, account_id: UUID, payload) -> AccountReadModel:
        portfolio_id = payload.portfolio_id
        assert portfolio_id is not None
        self.accounts[account_id]["portfolio_id"] = str(portfolio_id)
        self.updated_accounts.append((person_id, account_id, portfolio_id))
        return AccountReadModel.model_validate(self.accounts[account_id])

    async def _request_portfolio_service(self, method: str, path: str, **kwargs) -> dict:
        portfolio_id = path.rsplit("/", 1)[-1]
        return {
            "portfolio_id": portfolio_id,
            "person_id": str(PERSON_ID),
            "display_name": "Depot Gleich",
            "created_at": "2026-03-01T00:00:00+00:00",
            "updated_at": "2026-03-01T00:00:00+00:00",
            "holdings": [],
        }


def _account(account_id: UUID, *, label: str, portfolio_id: UUID | None) -> dict:
    return {
        "account_id": str(account_id),
        "person_id": str(PERSON_ID),
        "bank_id": "30000000-0000-0000-0000-000000000001",
        "account_type": "depot",
        "label": label,
        "balance": "100.00",
        "currency": "EUR",
        "created_at": "2026-03-01T00:00:00+00:00",
        "updated_at": "2026-03-01T00:00:00+00:00",
        "portfolio_id": str(portfolio_id) if portfolio_id is not None else None,
    }


def test_depot_portfolio_binding_uses_account_id_for_duplicate_depot_names() -> None:
    service = BindingGatewayService(
        {
            ACCOUNT_1: _account(ACCOUNT_1, label="Depot Gleich", portfolio_id=PORTFOLIO_1),
            ACCOUNT_2: _account(ACCOUNT_2, label="Depot Gleich", portfolio_id=PORTFOLIO_2),
        }
    )

    first = asyncio.run(service.get_depot_portfolio(PERSON_ID, ACCOUNT_1))
    second = asyncio.run(service.get_depot_portfolio(PERSON_ID, ACCOUNT_2))

    assert str(first.portfolio_id) == str(PORTFOLIO_1)
    assert str(second.portfolio_id) == str(PORTFOLIO_2)
    assert service.created_portfolios == []


def test_depot_rename_keeps_existing_portfolio_binding() -> None:
    service = BindingGatewayService(
        {
            ACCOUNT_1: _account(ACCOUNT_1, label="Depot Neu", portfolio_id=PORTFOLIO_1),
        }
    )

    portfolio = asyncio.run(service.get_depot_portfolio(PERSON_ID, ACCOUNT_1))

    assert str(portfolio.portfolio_id) == str(PORTFOLIO_1)
    assert service.created_portfolios == []


def test_depot_without_binding_gets_portfolio_id_persisted_on_account() -> None:
    service = BindingGatewayService(
        {
            ACCOUNT_1: _account(ACCOUNT_1, label="Depot Neu", portfolio_id=None),
        }
    )

    portfolio = asyncio.run(service.get_depot_portfolio(PERSON_ID, ACCOUNT_1))

    assert str(portfolio.portfolio_id) == str(PORTFOLIO_2)
    assert service.accounts[ACCOUNT_1]["portfolio_id"] == str(PORTFOLIO_2)
    assert service.updated_accounts == [(PERSON_ID, ACCOUNT_1, PORTFOLIO_2)]
