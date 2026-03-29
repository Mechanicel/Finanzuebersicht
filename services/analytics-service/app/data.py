from __future__ import annotations

from uuid import UUID

from app.models import PersonSnapshots

PERSON_SNAPSHOT_DATA: dict[UUID, PersonSnapshots] = {
    UUID("00000000-0000-0000-0000-000000000101"): PersonSnapshots.model_validate(
        {
            "person_id": "00000000-0000-0000-0000-000000000101",
            "snapshots": [
                {
                    "date": "2025-10-31",
                    "total_value": 120000,
                    "holdings": {"Stocks": 70000, "Bonds": 30000, "Cash": 20000},
                },
                {
                    "date": "2025-11-30",
                    "total_value": 123500,
                    "holdings": {"Stocks": 73000, "Bonds": 30500, "Cash": 20000},
                },
                {
                    "date": "2025-12-31",
                    "total_value": 128200,
                    "holdings": {"Stocks": 76000, "Bonds": 31200, "Cash": 21000},
                },
                {
                    "date": "2026-01-31",
                    "total_value": 131400,
                    "holdings": {"Stocks": 79000, "Bonds": 31400, "Cash": 21000},
                },
                {
                    "date": "2026-02-28",
                    "total_value": 134900,
                    "holdings": {"Stocks": 82000, "Bonds": 31900, "Cash": 21000},
                },
            ],
        }
    ),
    UUID("00000000-0000-0000-0000-000000000102"): PersonSnapshots.model_validate(
        {
            "person_id": "00000000-0000-0000-0000-000000000102",
            "snapshots": [
                {
                    "date": "2025-10-31",
                    "total_value": 89000,
                    "holdings": {"Stocks": 42000, "ETFs": 23000, "Cash": 24000},
                },
                {
                    "date": "2025-11-30",
                    "total_value": 90500,
                    "holdings": {"Stocks": 43500, "ETFs": 23000, "Cash": 24000},
                },
                {
                    "date": "2025-12-31",
                    "total_value": 92600,
                    "holdings": {"Stocks": 45000, "ETFs": 23500, "Cash": 24100},
                },
                {
                    "date": "2026-01-31",
                    "total_value": 93800,
                    "holdings": {"Stocks": 45600, "ETFs": 24000, "Cash": 24200},
                },
                {
                    "date": "2026-02-28",
                    "total_value": 95400,
                    "holdings": {"Stocks": 46800, "ETFs": 24200, "Cash": 24400},
                },
            ],
        }
    ),
}
