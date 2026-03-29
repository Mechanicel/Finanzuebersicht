from __future__ import annotations

from functools import lru_cache

from app.repositories import InMemoryPortfolioRepository, PortfolioRepository
from app.service import PortfolioService


@lru_cache(maxsize=1)
def get_repository() -> PortfolioRepository:
    return InMemoryPortfolioRepository()


def get_portfolio_service() -> PortfolioService:
    return PortfolioService(repository=get_repository())
