from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import HTTPException, status

from app.models import (
    Holding,
    HoldingInput,
    HoldingsReplaceRequest,
    HoldingsResponse,
    HoldingSnapshot,
    Portfolio,
    PortfolioDetailResponse,
    ResponseMode,
    SnapshotCreateRequest,
    SnapshotSummary,
    SnapshotsResponse,
)
from app.repositories import PortfolioRepository


class PortfolioService:
    def __init__(self, repository: PortfolioRepository) -> None:
        self.repository = repository

    def get_portfolio(self, portfolio_id: UUID, *, include_history: bool, mode: ResponseMode) -> PortfolioDetailResponse:
        portfolio = self.repository.get_by_portfolio_id(portfolio_id)
        if portfolio is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio nicht gefunden")
        return self._to_portfolio_response(portfolio, include_history=include_history, mode=mode)

    def get_account_portfolio(self, account_id: UUID, *, include_history: bool, mode: ResponseMode) -> PortfolioDetailResponse:
        portfolio = self.repository.get_by_account_id(account_id)
        return self._to_portfolio_response(portfolio, include_history=include_history, mode=mode)

    def put_holdings(self, account_id: UUID, payload: HoldingsReplaceRequest) -> HoldingsResponse:
        portfolio = self.repository.get_by_account_id(account_id)
        holdings = [
            Holding(
                portfolio_id=portfolio.portfolio_id,
                account_id=account_id,
                isin=item.isin,
                quantity=item.quantity,
                instrument_name=item.instrument_name,
            )
            for item in payload.holdings
        ]
        stored = self.repository.put_holdings(account_id, holdings)
        self._refresh_portfolio_aggregates(account_id)

        return HoldingsResponse(
            portfolio_id=portfolio.portfolio_id,
            account_id=account_id,
            display_name=portfolio.display_name,
            holdings_count=len(stored),
            total_quantity_summary=self._sum_quantity([item.quantity for item in stored]),
            holdings=[self._holding_to_input(item) for item in stored],
        )

    def list_holdings(self, account_id: UUID, *, mode: ResponseMode) -> HoldingsResponse:
        portfolio = self.repository.get_by_account_id(account_id)
        holdings = self.repository.list_holdings(account_id)
        response_holdings = [self._holding_to_input(item) for item in holdings]
        if mode == ResponseMode.COMPACT:
            response_holdings = []

        return HoldingsResponse(
            portfolio_id=portfolio.portfolio_id,
            account_id=account_id,
            display_name=portfolio.display_name,
            holdings_count=len(holdings),
            total_quantity_summary=self._sum_quantity([item.quantity for item in holdings]),
            holdings=response_holdings,
        )

    def create_snapshot(self, account_id: UUID, payload: SnapshotCreateRequest) -> HoldingSnapshot:
        portfolio = self.repository.get_by_account_id(account_id)

        snapshot = HoldingSnapshot(
            portfolio_id=portfolio.portfolio_id,
            account_id=account_id,
            snapshot_date=payload.snapshot_date,
            note=payload.note,
            holdings=payload.holdings,
            holdings_count=len(payload.holdings),
            total_quantity_summary=self._sum_quantity([item.quantity for item in payload.holdings]),
        )
        created = self.repository.create_snapshot(account_id, snapshot)
        self._refresh_portfolio_aggregates(account_id)
        return created

    def list_snapshots(
        self,
        account_id: UUID,
        *,
        as_of: date | None,
        include_history: bool,
        mode: ResponseMode,
    ) -> SnapshotsResponse:
        portfolio = self.repository.get_by_account_id(account_id)
        snapshots = self.repository.list_snapshots(account_id)
        if as_of is not None:
            snapshots = [item for item in snapshots if item.snapshot_date <= as_of]

        if not include_history and snapshots:
            snapshots = [snapshots[-1]]

        latest = self._latest_snapshot_summary(snapshots)
        if mode == ResponseMode.COMPACT:
            snapshots = []

        return SnapshotsResponse(
            account_id=account_id,
            portfolio_id=portfolio.portfolio_id,
            display_name=portfolio.display_name,
            latest_snapshot_summary=latest,
            snapshots=snapshots,
        )

    def _to_portfolio_response(self, portfolio: Portfolio, *, include_history: bool, mode: ResponseMode) -> PortfolioDetailResponse:
        holdings = self.repository.list_holdings(portfolio.account_id)
        snapshots = self.repository.list_snapshots(portfolio.account_id)
        snapshot_summaries = [self._snapshot_summary(item) for item in snapshots]

        if not include_history and snapshot_summaries:
            snapshot_summaries = [snapshot_summaries[-1]]

        holdings_data: list[HoldingInput] | None = [self._holding_to_input(item) for item in holdings]
        if mode == ResponseMode.COMPACT:
            holdings_data = None
            snapshot_summaries = None

        return PortfolioDetailResponse(
            portfolio_id=portfolio.portfolio_id,
            account_id=portfolio.account_id,
            display_name=portfolio.display_name,
            account_summary=portfolio.account_summary,
            holdings_count=len(holdings),
            total_quantity_summary=self._sum_quantity([item.quantity for item in holdings]),
            latest_snapshot_summary=self._latest_snapshot_summary(snapshots),
            holdings=holdings_data,
            snapshots=snapshot_summaries,
        )

    def _refresh_portfolio_aggregates(self, account_id: UUID) -> None:
        portfolio = self.repository.get_by_account_id(account_id)
        holdings = self.repository.list_holdings(account_id)
        snapshots = self.repository.list_snapshots(account_id)

        portfolio.account_summary.holdings_count = len(holdings)
        portfolio.account_summary.total_quantity_summary = self._sum_quantity([item.quantity for item in holdings])
        portfolio.holdings_count = len(holdings)
        portfolio.total_quantity_summary = self._sum_quantity([item.quantity for item in holdings])
        portfolio.latest_snapshot_summary = self._latest_snapshot_summary(snapshots)

    @staticmethod
    def _holding_to_input(item: Holding) -> HoldingInput:
        return HoldingInput(isin=item.isin, quantity=item.quantity, instrument_name=item.instrument_name)

    @staticmethod
    def _sum_quantity(values: list[float]) -> float:
        return round(sum(values), 6)

    def _latest_snapshot_summary(self, snapshots: list[HoldingSnapshot]) -> SnapshotSummary | None:
        if not snapshots:
            return None
        return self._snapshot_summary(snapshots[-1])

    @staticmethod
    def _snapshot_summary(snapshot: HoldingSnapshot) -> SnapshotSummary:
        return SnapshotSummary(
            snapshot_id=snapshot.snapshot_id,
            snapshot_date=snapshot.snapshot_date,
            holdings_count=snapshot.holdings_count,
            total_quantity_summary=snapshot.total_quantity_summary,
            created_at=snapshot.created_at,
        )
