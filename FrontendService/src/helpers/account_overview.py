from __future__ import annotations

from datetime import date, datetime
from typing import Any



def parse_balance_entry(entry: str) -> tuple[str, float] | None:
    if not isinstance(entry, str) or ": " not in entry:
        return None
    date_str, value_str = entry.split(": ", 1)
    try:
        return date_str, float(value_str)
    except (TypeError, ValueError):
        return None


def parse_decimal_input(text: str) -> float | None:
    if text is None:
        return None
    cleaned = str(text).strip().replace(" ", "")
    if not cleaned:
        return None

    if "," in cleaned and "." in cleaned:
        if cleaned.rfind(",") > cleaned.rfind("."):
            normalized = cleaned.replace(".", "").replace(",", ".")
        else:
            normalized = cleaned.replace(",", "")
    elif "," in cleaned:
        normalized = cleaned.replace(".", "").replace(",", ".")
    else:
        normalized = cleaned.replace(",", "")

    try:
        return float(normalized)
    except (TypeError, ValueError):
        return None


def get_latest_balance_entry_for_account(account: dict[str, Any]) -> tuple[str | None, float]:
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


def build_account_label(account: dict[str, Any]) -> str:
    bank = account.get("Bank", "Unbekannte Bank")
    kontotyp = account.get("Kontotyp", "Konto")
    nummer = account.get("Kontonummer") or account.get("Deponummer") or "–"
    return f"{bank} · {kontotyp} · {nummer}"


def normalize_depot_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[int, dict[str, str]]]:
    normalized: list[dict[str, Any]] = []
    errors: dict[int, dict[str, str]] = {}

    for idx, row in enumerate(rows):
        isin = str(row.get("isin", "")).strip()
        menge_text = str(row.get("menge", "")).strip()

        if not isin and not menge_text:
            continue

        row_errors: dict[str, str] = {}
        menge_value = None

        if isin and not menge_text:
            row_errors["menge"] = "Menge fehlt."
        elif menge_text:
            menge_value = parse_decimal_input(menge_text)
            if menge_value is None:
                row_errors["menge"] = "Menge muss numerisch sein."

        if menge_text and not isin:
            row_errors["isin"] = "ISIN fehlt."

        if row_errors:
            errors[idx] = row_errors
            continue

        normalized.append({"ISIN": isin, "Menge": menge_value})

    return normalized, errors


def validate_overview_inputs(
    balance_inputs: list[dict[str, Any]],
    depot_inputs: list[dict[str, Any]],
) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    balance_errors: dict[int, str] = {}
    depot_errors: dict[int, dict[int, dict[str, str]]] = {}
    messages: list[str] = []

    for item in balance_inputs:
        account_key = item["account_key"]
        value_text = str(item.get("value", "")).strip()
        value = parse_decimal_input(value_text)
        if not value_text:
            balance_errors[account_key] = "Bitte Saldo eingeben."
            continue
        if value is None:
            balance_errors[account_key] = "Ungültige Zahl (z. B. 1234,56)."
            continue
        entries.append({"konto": item["konto"], "balance": value})

    for item in depot_inputs:
        account_key = item["account_key"]
        normalized_rows, row_errors = normalize_depot_rows(item.get("rows", []))
        if row_errors:
            depot_errors[account_key] = row_errors
            continue
        entries.append({"konto": item["konto"], "details": normalized_rows})

    if balance_errors:
        messages.append("Mindestens ein Saldo ist leer oder ungültig.")
    if depot_errors:
        messages.append("Mindestens eine Depotposition ist unvollständig oder ungültig.")

    return {
        "entries": entries,
        "balance_errors": balance_errors,
        "depot_errors": depot_errors,
        "messages": messages,
        "is_valid": not balance_errors and not depot_errors,
    }


def latest_snapshot_date(accounts: list[dict[str, Any]]) -> date | None:
    latest: date | None = None
    for account in accounts:
        date_str, _ = get_latest_balance_entry_for_account(account)
        if not date_str:
            continue
        try:
            parsed = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            continue
        if latest is None or parsed > latest:
            latest = parsed
    return latest
