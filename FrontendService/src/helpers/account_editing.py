from __future__ import annotations

import logging
from datetime import date
from typing import Any

logger = logging.getLogger(__name__)


def parse_balance_entry(entry: str) -> tuple[str, float] | None:
    if not isinstance(entry, str) or ": " not in entry:
        return None
    date_str, value_str = entry.split(": ", 1)
    try:
        return date_str, float(value_str)
    except (TypeError, ValueError):
        return None


def get_latest_balance_entry(account: dict[str, Any]) -> tuple[str | None, float]:
    latest_date = None
    latest_balance = 0.0
    for raw_entry in account.get("Kontostaende", []) or []:
        parsed = parse_balance_entry(raw_entry)
        if not parsed:
            continue
        entry_date, value = parsed
        if latest_date is None or entry_date > latest_date:
            latest_date = entry_date
            latest_balance = value
    return latest_date, latest_balance


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
