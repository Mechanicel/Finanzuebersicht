from __future__ import annotations

import logging
from datetime import date
from typing import Any

from src.helpers.account_overview import get_latest_balance_entry_for_account, parse_balance_entry

logger = logging.getLogger(__name__)


def get_latest_balance_entry(account: dict[str, Any]) -> tuple[str | None, float]:
    return get_latest_balance_entry_for_account(account)


def update_latest_balance_entry(account: dict[str, Any], balance: float, reference_date: date | None) -> None:
    entries = account.get("Kontostaende", []) or []
    parsed_entries: list[tuple[str, float]] = []
    for raw_entry in entries:
        parsed = parse_balance_entry(raw_entry)
        if parsed:
            parsed_entries.append(parsed)

    if parsed_entries:
        latest_date = max(item[0] for item in parsed_entries)
    else:
        latest_date = (reference_date or date.today()).strftime("%Y-%m-%d")

    value_map = {entry_date: entry_value for entry_date, entry_value in parsed_entries}
    value_map[latest_date] = balance
    account["Kontostaende"] = [f"{entry_date}: {value_map[entry_date]:.2f}" for entry_date in sorted(value_map)]


def recalculate_depot_after_account_edit(account_controller, selected_person: dict[str, Any], selected_date: date | None) -> bool:
    reference_date = selected_date or date.today()
    try:
        account_controller.calculate_depot(selected_person, reference_date)
        return True
    except Exception:
        logger.exception("Depot-Neuberechnung nach Konto-Bearbeitung fehlgeschlagen")
        return False
