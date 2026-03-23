def filter_bank_names(bank_names: list[str], search_term: str) -> list[str]:
    term = (search_term or "").strip().casefold()
    if not term:
        return bank_names
    return [bank for bank in bank_names if term in bank.casefold()]


def extract_latest_balance(konto: dict) -> float:
    entries = konto.get("Kontostaende", [])
    if entries:
        try:
            return float(entries[-1].split(": ")[1])
        except Exception:
            return 0.0
    if konto.get("Kontotyp") == "Depot":
        details = konto.get("DepotDetails", [])
        return sum(float(detail.get("value", 0.0) or 0.0) for detail in details if isinstance(detail, dict))
    return 0.0
