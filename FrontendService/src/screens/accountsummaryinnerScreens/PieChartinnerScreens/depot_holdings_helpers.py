from __future__ import annotations

from typing import Any

UNKNOWN_GROUP_LABEL = "Unbekannt"
GROUP_BY_OPTIONS = ("position", "sector", "country", "currency")


def to_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def build_holdings_rows(
    depot_details: list[dict[str, Any]] | None,
    quotes_by_isin: dict[str, float] | None,
    company_by_isin: dict[str, str] | None,
    metadata_by_isin: dict[str, dict[str, Any]] | None,
) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []

    for detail in depot_details or []:
        isin = str((detail or {}).get("ISIN") or "").strip()
        if not isin:
            warnings.append("Depotposition ohne ISIN wurde übersprungen.")
            continue

        quantity = to_float((detail or {}).get("Menge"))
        if quantity is None:
            warnings.append(f"Ungültige Menge für {isin}; Position wird mit 0 berechnet.")
            quantity = 0.0

        price = to_float((quotes_by_isin or {}).get(isin))
        if price is None:
            warnings.append(f"Kein Preis für {isin} gefunden; Preis wird mit 0 berechnet.")
            price = 0.0

        metadata = (metadata_by_isin or {}).get(isin) or {}
        currency = metadata.get("currency") or "EUR"
        name = (company_by_isin or {}).get(isin) or metadata.get("name") or isin

        row = {
            "name": name,
            "isin": isin,
            "quantity": quantity,
            "price": price,
            "market_value": quantity * price,
            "sector": metadata.get("sector") or UNKNOWN_GROUP_LABEL,
            "country": metadata.get("country") or UNKNOWN_GROUP_LABEL,
            "currency": currency,
            "provider": metadata.get("provider"),
            "as_of": metadata.get("as_of"),
            "coverage": metadata.get("coverage"),
        }
        rows.append(row)

    return rows, warnings


def with_weight_percent(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    total_value = sum(float(row.get("market_value") or 0.0) for row in rows)
    enriched: list[dict[str, Any]] = []
    for row in rows:
        cloned = dict(row)
        value = float(cloned.get("market_value") or 0.0)
        cloned["weight_pct"] = (value / total_value * 100.0) if total_value > 0 else 0.0
        enriched.append(cloned)
    return enriched


def sort_rows(rows: list[dict[str, Any]], key: str = "market_value", reverse: bool = True) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda row: float(row.get(key) or 0.0), reverse=reverse)


def summarize_groups(rows: list[dict[str, Any]], group_by: str) -> list[dict[str, Any]]:
    if group_by not in GROUP_BY_OPTIONS:
        group_by = "position"

    if group_by == "position":
        grouped = [
            {
                "group": row.get("name") or row.get("isin") or UNKNOWN_GROUP_LABEL,
                "value": float(row.get("market_value") or 0.0),
                "weight_pct": float(row.get("weight_pct") or 0.0),
                "count": 1,
                "isins": [row.get("isin")],
            }
            for row in rows
        ]
        return sort_rows(grouped, key="value", reverse=True)

    buckets: dict[str, dict[str, Any]] = {}
    for row in rows:
        bucket_name = str(row.get(group_by) or UNKNOWN_GROUP_LABEL)
        bucket = buckets.setdefault(bucket_name, {"group": bucket_name, "value": 0.0, "weight_pct": 0.0, "count": 0, "isins": []})
        bucket["value"] += float(row.get("market_value") or 0.0)
        bucket["weight_pct"] += float(row.get("weight_pct") or 0.0)
        bucket["count"] += 1
        isin = row.get("isin")
        if isin:
            bucket["isins"].append(isin)

    return sort_rows(list(buckets.values()), key="value", reverse=True)
