from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from uuid import UUID

from app.models import Holding, HoldingSnapshot, Portfolio


class PortfolioRepository(ABC):
    @abstractmethod
    def get_by_portfolio_id(self, portfolio_id: UUID) -> Portfolio | None: ...

    @abstractmethod
    def get_by_account_id(self, account_id: UUID) -> Portfolio: ...

    @abstractmethod
    def put_holdings(self, account_id: UUID, holdings: list[Holding]) -> list[Holding]: ...

    @abstractmethod
    def list_holdings(self, account_id: UUID) -> list[Holding]: ...

    @abstractmethod
    def create_snapshot(self, account_id: UUID, snapshot: HoldingSnapshot) -> HoldingSnapshot: ...

    @abstractmethod
    def list_snapshots(self, account_id: UUID) -> list[HoldingSnapshot]: ...


class InMemoryPortfolioRepository(PortfolioRepository):
    def __init__(self) -> None:
        self._portfolios_by_account: dict[UUID, Portfolio] = {}
        self._portfolio_to_account: dict[UUID, UUID] = {}
        self._holdings_by_account: dict[UUID, dict[str, Holding]] = {}
        self._snapshots_by_account: dict[UUID, list[HoldingSnapshot]] = {}

    def get_by_portfolio_id(self, portfolio_id: UUID) -> Portfolio | None:
        account_id = self._portfolio_to_account.get(portfolio_id)
        if account_id is None:
            return None
        return self._portfolios_by_account.get(account_id)

    def get_by_account_id(self, account_id: UUID) -> Portfolio:
        portfolio = self._portfolios_by_account.get(account_id)
        if portfolio is not None:
            return portfolio

        created = Portfolio(
            account_id=account_id,
            display_name=f"Depot {str(account_id)[:8]}",
            account_summary={"account_id": account_id, "holdings_count": 0, "total_quantity_summary": 0},
            holdings_count=0,
            total_quantity_summary=0,
        )
        self._portfolios_by_account[account_id] = created
        self._portfolio_to_account[created.portfolio_id] = account_id
        self._holdings_by_account.setdefault(account_id, {})
        self._snapshots_by_account.setdefault(account_id, [])
        return created

    def put_holdings(self, account_id: UUID, holdings: list[Holding]) -> list[Holding]:
        self._holdings_by_account[account_id] = {item.isin: item for item in holdings}
        portfolio = self.get_by_account_id(account_id)
        updated_portfolio = portfolio.model_copy(
            update={
                "updated_at": datetime.now(timezone.utc),
            }
        )
        self._portfolios_by_account[account_id] = updated_portfolio
        return list(self._holdings_by_account[account_id].values())

    def list_holdings(self, account_id: UUID) -> list[Holding]:
        return list(self._holdings_by_account.get(account_id, {}).values())

    def create_snapshot(self, account_id: UUID, snapshot: HoldingSnapshot) -> HoldingSnapshot:
        snapshots = self._snapshots_by_account.setdefault(account_id, [])
        snapshots.append(snapshot)
        snapshots.sort(key=lambda item: (item.snapshot_date, item.created_at))
        return snapshot

    def list_snapshots(self, account_id: UUID) -> list[HoldingSnapshot]:
        return list(self._snapshots_by_account.get(account_id, []))
