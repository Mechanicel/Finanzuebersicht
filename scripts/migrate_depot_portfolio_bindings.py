from __future__ import annotations

import argparse
import os
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

from pymongo import MongoClient


def _mongo_uri() -> str:
    return "mongodb://finanzuebersicht:SchweresPw124FFASDF@localhost:27017/finanzuebersicht?authSource=admin"


def _group_by_person_and_name(items: list[dict[str, Any]]) -> dict[tuple[str, str], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for item in items:
        label = str(item.get("label") or item.get("display_name") or "").strip()
        if label:
            grouped[(str(item["person_id"]), label)].append(item)
    return grouped


def _conflict_reason(
    same_name_accounts: list[dict[str, Any]],
    same_name_portfolios: list[dict[str, Any]],
) -> str:
    if len(same_name_accounts) > 1:
        return "duplicate_depot_label"
    if len(same_name_portfolios) > 1:
        return "duplicate_portfolio_display_name"
    return "no_portfolio_match"


def migrate(*, apply: bool) -> dict[str, int]:
    client = MongoClient(_mongo_uri())
    database = client[os.getenv("MONGO_DATABASE", "finanzuebersicht")]
    accounts_collection = database[os.getenv("MONGO_ACCOUNTS_COLLECTION", "accounts")]
    portfolios_collection = database[os.getenv("MONGO_PORTFOLIOS_COLLECTION", "portfolios")]

    depot_accounts = list(accounts_collection.find({"account_type": "depot"}))
    portfolios = list(portfolios_collection.find({}))
    accounts_by_person_and_name = _group_by_person_and_name(depot_accounts)
    portfolios_by_person_and_name = _group_by_person_and_name(portfolios)

    checked_at = datetime.now(UTC).isoformat()
    stats = {"bound": 0, "conflict": 0, "already_bound": 0}

    for account in depot_accounts:
        if account.get("portfolio_id"):
            stats["already_bound"] += 1
            continue

        key = (str(account["person_id"]), str(account.get("label", "")).strip())
        same_name_accounts = accounts_by_person_and_name.get(key, [])
        same_name_portfolios = portfolios_by_person_and_name.get(key, [])

        if len(same_name_accounts) == 1 and len(same_name_portfolios) == 1:
            stats["bound"] += 1
            if apply:
                accounts_collection.update_one(
                    {"_id": account["_id"]},
                    {
                        "$set": {"portfolio_id": str(same_name_portfolios[0]["portfolio_id"])},
                        "$unset": {"portfolio_binding_migration_status": ""},
                    },
                )
            continue

        stats["conflict"] += 1
        if apply:
            accounts_collection.update_one(
                {"_id": account["_id"]},
                {
                    "$set": {
                        "portfolio_binding_migration_status": {
                            "status": "conflict",
                            "reason": _conflict_reason(same_name_accounts, same_name_portfolios),
                            "matched_portfolio_ids": [
                                str(portfolio["portfolio_id"]) for portfolio in same_name_portfolios
                            ],
                            "checked_at": checked_at,
                        }
                    }
                },
            )

    return stats


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bind existing depot accounts to portfolios via account.portfolio_id."
    )
    parser.add_argument("--apply", action="store_true", help="Write changes. Without this flag only prints a dry run.")
    args = parser.parse_args()

    stats = migrate(apply=args.apply)
    mode = "applied" if args.apply else "dry-run"
    print(f"{mode}: bound={stats['bound']} conflict={stats['conflict']} already_bound={stats['already_bound']}")


if __name__ == "__main__":
    main()
