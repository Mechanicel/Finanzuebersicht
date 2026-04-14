from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status

from app.models import (
    BenchmarkConfigPayload,
    BenchmarkConfigReadModel,
    Holding,
    HoldingCreatePayload,
    HoldingsRefreshStubResponse,
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

    def get_benchmark_config(self, person_id: UUID) -> BenchmarkConfigReadModel:
        doc = self.repository.get_benchmark_config(person_id)
        if doc is None:
            return BenchmarkConfigReadModel(person_id=person_id)
        return BenchmarkConfigReadModel.model_validate(doc)

    def set_benchmark_config(self, person_id: UUID, payload: BenchmarkConfigPayload) -> BenchmarkConfigReadModel:
        if payload.components:
            total = sum(c.weight for c in payload.components)
            if abs(total - 100.0) > 0.01:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Benchmark-Gewichte müssen sich auf 100 summieren (erhalten: {total:.2f})",
                )
        now = datetime.now(timezone.utc)
        config_doc = {
            "person_id": str(person_id),
            "components": [c.model_dump() for c in payload.components],
            "updated_at": now.isoformat(),
        }
        self.repository.set_benchmark_config(person_id, config_doc)
        return BenchmarkConfigReadModel(
            person_id=person_id,
            components=payload.components,
            updated_at=now,
        )

    def refresh_holdings_prices(self, portfolio_id: UUID) -> HoldingsRefreshStubResponse:
        portfolio = self.repository.get_portfolio(portfolio_id)
        if portfolio is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio nicht gefunden")
        return HoldingsRefreshStubResponse(
            portfolio_id=portfolio_id,
            status="not_implemented_yet",
            accepted=False,
            detail="Technischer Refresh-Flow vorbereitet. Marktpreislogik folgt in einem späteren Schritt.",
        )
