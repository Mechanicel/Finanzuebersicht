from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import date
from uuid import UUID

from pymongo import ASCENDING
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import PyMongoError

from app.models import Holding, Portfolio


class PortfolioRepositoryError(Exception):
    pass


class PortfolioRepository(ABC):
    @abstractmethod
    def create_portfolio(self, portfolio: Portfolio) -> Portfolio: ...

    @abstractmethod
    def list_person_portfolios(self, person_id: UUID) -> list[Portfolio]: ...

    @abstractmethod
    def get_portfolio(self, portfolio_id: UUID) -> Portfolio | None: ...

    @abstractmethod
    def create_holding(self, holding: Holding) -> Holding: ...

    @abstractmethod
    def list_holdings(self, portfolio_id: UUID) -> list[Holding]: ...

    @abstractmethod
    def get_holding(self, portfolio_id: UUID, holding_id: UUID) -> Holding | None: ...

    @abstractmethod
    def update_holding(self, holding: Holding) -> Holding: ...

    @abstractmethod
    def delete_holding(self, portfolio_id: UUID, holding_id: UUID) -> bool: ...

    @abstractmethod
    def get_benchmark_config(self, person_id: UUID) -> dict | None: ...

    @abstractmethod
    def set_benchmark_config(self, person_id: UUID, config_doc: dict) -> None: ...


class InMemoryPortfolioRepository(PortfolioRepository):
    def __init__(self) -> None:
        self._portfolios: dict[UUID, Portfolio] = {}
        self._person_portfolios: dict[UUID, list[UUID]] = defaultdict(list)
        self._holdings_by_portfolio: dict[UUID, dict[UUID, Holding]] = defaultdict(dict)
        self._benchmark_configs: dict[UUID, dict] = {}

    def create_portfolio(self, portfolio: Portfolio) -> Portfolio:
        self._portfolios[portfolio.portfolio_id] = portfolio
        self._person_portfolios[portfolio.person_id].append(portfolio.portfolio_id)
        return portfolio

    def list_person_portfolios(self, person_id: UUID) -> list[Portfolio]:
        portfolio_ids = self._person_portfolios.get(person_id, [])
        return [self._portfolios[item] for item in portfolio_ids]

    def get_portfolio(self, portfolio_id: UUID) -> Portfolio | None:
        return self._portfolios.get(portfolio_id)

    def create_holding(self, holding: Holding) -> Holding:
        self._holdings_by_portfolio[holding.portfolio_id][holding.holding_id] = holding
        return holding

    def list_holdings(self, portfolio_id: UUID) -> list[Holding]:
        return list(self._holdings_by_portfolio.get(portfolio_id, {}).values())

    def get_holding(self, portfolio_id: UUID, holding_id: UUID) -> Holding | None:
        return self._holdings_by_portfolio.get(portfolio_id, {}).get(holding_id)

    def update_holding(self, holding: Holding) -> Holding:
        self._holdings_by_portfolio[holding.portfolio_id][holding.holding_id] = holding
        return holding

    def delete_holding(self, portfolio_id: UUID, holding_id: UUID) -> bool:
        deleted = self._holdings_by_portfolio.get(portfolio_id, {}).pop(holding_id, None)
        return deleted is not None

    def get_benchmark_config(self, person_id: UUID) -> dict | None:
        return self._benchmark_configs.get(person_id)

    def set_benchmark_config(self, person_id: UUID, config_doc: dict) -> None:
        self._benchmark_configs[person_id] = config_doc


class MongoPortfolioRepository(PortfolioRepository):
    def __init__(
        self,
        database: Database,
        *,
        portfolio_collection: str,
        holding_collection: str,
        benchmark_config_collection: str = "benchmark_configs",
    ) -> None:
        self._portfolios: Collection = database[portfolio_collection]
        self._holdings: Collection = database[holding_collection]
        self._benchmark_configs: Collection = database[benchmark_config_collection]
        self._ensure_indexes()

    def _ensure_indexes(self) -> None:
        self._portfolios.create_index([("portfolio_id", ASCENDING)], unique=True)
        self._portfolios.create_index([("person_id", ASCENDING), ("created_at", ASCENDING)])
        self._holdings.create_index([("portfolio_id", ASCENDING), ("holding_id", ASCENDING)], unique=True)
        self._holdings.create_index([("portfolio_id", ASCENDING), ("created_at", ASCENDING)])
        self._benchmark_configs.create_index([("person_id", ASCENDING)], unique=True)

    def create_portfolio(self, portfolio: Portfolio) -> Portfolio:
        try:
            self._portfolios.insert_one(self._portfolio_to_doc(portfolio))
            return portfolio
        except PyMongoError as exc:
            raise PortfolioRepositoryError("Failed to create portfolio") from exc

    def list_person_portfolios(self, person_id: UUID) -> list[Portfolio]:
        try:
            docs = self._portfolios.find({"person_id": str(person_id)}, {"_id": 0}).sort("created_at", ASCENDING)
            return [Portfolio.model_validate(doc) for doc in docs]
        except PyMongoError as exc:
            raise PortfolioRepositoryError("Failed to list portfolios") from exc

    def get_portfolio(self, portfolio_id: UUID) -> Portfolio | None:
        try:
            doc = self._portfolios.find_one({"portfolio_id": str(portfolio_id)}, {"_id": 0})
        except PyMongoError as exc:
            raise PortfolioRepositoryError("Failed to load portfolio") from exc
        if doc is None:
            return None
        return Portfolio.model_validate(doc)

    def create_holding(self, holding: Holding) -> Holding:
        try:
            self._holdings.insert_one(self._holding_to_doc(holding))
            return holding
        except PyMongoError as exc:
            raise PortfolioRepositoryError("Failed to create holding") from exc

    def list_holdings(self, portfolio_id: UUID) -> list[Holding]:
        try:
            docs = self._holdings.find({"portfolio_id": str(portfolio_id)}, {"_id": 0}).sort("created_at", ASCENDING)
            return [self._holding_from_doc(doc) for doc in docs]
        except PyMongoError as exc:
            raise PortfolioRepositoryError("Failed to list holdings") from exc

    def get_holding(self, portfolio_id: UUID, holding_id: UUID) -> Holding | None:
        try:
            doc = self._holdings.find_one(
                {"portfolio_id": str(portfolio_id), "holding_id": str(holding_id)},
                {"_id": 0},
            )
        except PyMongoError as exc:
            raise PortfolioRepositoryError("Failed to load holding") from exc
        if doc is None:
            return None
        return self._holding_from_doc(doc)

    def update_holding(self, holding: Holding) -> Holding:
        try:
            self._holdings.replace_one(
                {"portfolio_id": str(holding.portfolio_id), "holding_id": str(holding.holding_id)},
                self._holding_to_doc(holding),
                upsert=False,
            )
            return holding
        except PyMongoError as exc:
            raise PortfolioRepositoryError("Failed to update holding") from exc

    def delete_holding(self, portfolio_id: UUID, holding_id: UUID) -> bool:
        try:
            result = self._holdings.delete_one({"portfolio_id": str(portfolio_id), "holding_id": str(holding_id)})
            return result.deleted_count > 0
        except PyMongoError as exc:
            raise PortfolioRepositoryError("Failed to delete holding") from exc

    def get_benchmark_config(self, person_id: UUID) -> dict | None:
        try:
            doc = self._benchmark_configs.find_one({"person_id": str(person_id)}, {"_id": 0})
            return dict(doc) if doc is not None else None
        except PyMongoError as exc:
            raise PortfolioRepositoryError("Failed to load benchmark config") from exc

    def set_benchmark_config(self, person_id: UUID, config_doc: dict) -> None:
        try:
            self._benchmark_configs.replace_one(
                {"person_id": str(person_id)},
                config_doc,
                upsert=True,
            )
        except PyMongoError as exc:
            raise PortfolioRepositoryError("Failed to save benchmark config") from exc

    @staticmethod
    def _portfolio_to_doc(portfolio: Portfolio) -> dict[str, object]:
        return {
            "portfolio_id": str(portfolio.portfolio_id),
            "person_id": str(portfolio.person_id),
            "display_name": portfolio.display_name,
            "created_at": portfolio.created_at,
            "updated_at": portfolio.updated_at,
        }

    @staticmethod
    def _holding_to_doc(holding: Holding) -> dict[str, object]:
        return {
            "holding_id": str(holding.holding_id),
            "portfolio_id": str(holding.portfolio_id),
            "symbol": holding.symbol,
            "isin": holding.isin,
            "wkn": holding.wkn,
            "company_name": holding.company_name,
            "display_name": holding.display_name,
            "quantity": holding.quantity,
            "acquisition_price": holding.acquisition_price,
            "currency": holding.currency,
            "buy_date": holding.buy_date.isoformat(),
            "notes": holding.notes,
            "created_at": holding.created_at,
            "updated_at": holding.updated_at,
        }

    @staticmethod
    def _holding_from_doc(doc: dict[str, object]) -> Holding:
        normalized = dict(doc)
        normalized["buy_date"] = date.fromisoformat(str(normalized["buy_date"]))
        return Holding.model_validate(normalized)
