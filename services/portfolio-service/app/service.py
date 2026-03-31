from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status

from app.models import (
    Holding,
    HoldingCreatePayload,
    HoldingUpdatePayload,
    Portfolio,
    PortfolioCreatePayload,
    PortfolioDetailResponse,
    PortfolioListResponse,
)
from app.repositories import PortfolioRepository


class PortfolioService:
    def __init__(self, repository: PortfolioRepository) -> None:
        self.repository = repository

    def create_portfolio(self, payload: PortfolioCreatePayload) -> Portfolio:
        portfolio = Portfolio(person_id=payload.person_id, display_name=payload.display_name)
        return self.repository.create_portfolio(portfolio)

    def list_person_portfolios(self, person_id: UUID) -> PortfolioListResponse:
        items = self.repository.list_person_portfolios(person_id)
        return PortfolioListResponse(items=items, total=len(items))

    def get_portfolio_detail(self, portfolio_id: UUID) -> PortfolioDetailResponse:
        portfolio = self.repository.get_portfolio(portfolio_id)
        if portfolio is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio nicht gefunden")
        holdings = self.repository.list_holdings(portfolio_id)
        return PortfolioDetailResponse(**portfolio.model_dump(), holdings=holdings)

    def create_holding(self, portfolio_id: UUID, payload: HoldingCreatePayload) -> Holding:
        portfolio = self.repository.get_portfolio(portfolio_id)
        if portfolio is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio nicht gefunden")

        holding = Holding(portfolio_id=portfolio_id, **payload.model_dump())
        return self.repository.create_holding(holding)

    def update_holding(self, portfolio_id: UUID, holding_id: UUID, payload: HoldingUpdatePayload) -> Holding:
        portfolio = self.repository.get_portfolio(portfolio_id)
        if portfolio is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio nicht gefunden")

        holding = self.repository.get_holding(portfolio_id, holding_id)
        if holding is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Holding nicht gefunden")

        updates = payload.model_dump(exclude_unset=True)
        updated = holding.model_copy(update={**updates, "updated_at": datetime.now(timezone.utc)})
        return self.repository.update_holding(updated)

    def delete_holding(self, portfolio_id: UUID, holding_id: UUID) -> None:
        portfolio = self.repository.get_portfolio(portfolio_id)
        if portfolio is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio nicht gefunden")

        deleted = self.repository.delete_holding(portfolio_id, holding_id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Holding nicht gefunden")
