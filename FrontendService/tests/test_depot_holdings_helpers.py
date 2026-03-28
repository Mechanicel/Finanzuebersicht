from src.screens.accountsummaryinnerScreens.PieChartinnerScreens.depot_holdings_helpers import (
    UNKNOWN_GROUP_LABEL,
    build_holdings_rows,
    sort_rows,
    summarize_groups,
    with_weight_percent,
)


def test_build_holdings_rows_and_weights_handles_invalid_quantity_and_missing_metadata():
    depot_details = [
        {"ISIN": "AAA", "Menge": "2"},
        {"ISIN": "BBB", "Menge": "bad"},
    ]
    quotes = {"AAA": 10.0, "BBB": 20.0}
    companies = {"AAA": "Alpha"}
    metadata = {
        "AAA": {"sector": "Tech", "country": "US", "currency": "USD"},
        "BBB": {},
    }

    rows, warnings = build_holdings_rows(depot_details, quotes, companies, metadata)
    weighted = with_weight_percent(rows)
    weighted = sort_rows(weighted, "market_value", reverse=True)

    assert len(weighted) == 2
    assert weighted[0]["isin"] == "AAA"
    assert weighted[0]["market_value"] == 20.0
    assert weighted[0]["weight_pct"] == 100.0
    assert weighted[1]["market_value"] == 0.0
    assert weighted[1]["sector"] == UNKNOWN_GROUP_LABEL
    assert any("Ungültige Menge" in msg for msg in warnings)


def test_grouping_by_sector_and_currency_sums_and_sorts():
    rows = with_weight_percent(
        [
            {"isin": "A", "name": "A", "market_value": 60.0, "sector": "Tech", "country": "US", "currency": "USD"},
            {"isin": "B", "name": "B", "market_value": 30.0, "sector": "Tech", "country": "DE", "currency": "EUR"},
            {"isin": "C", "name": "C", "market_value": 10.0, "sector": UNKNOWN_GROUP_LABEL, "country": "DE", "currency": "EUR"},
        ]
    )

    by_sector = summarize_groups(rows, "sector")
    by_currency = summarize_groups(rows, "currency")

    assert by_sector[0]["group"] == "Tech"
    assert by_sector[0]["value"] == 90.0
    assert by_sector[0]["count"] == 2
    assert by_currency[0]["group"] == "USD"
    assert by_currency[0]["value"] == 60.0
    assert by_currency[1]["group"] == "EUR"
    assert by_currency[1]["value"] == 40.0
