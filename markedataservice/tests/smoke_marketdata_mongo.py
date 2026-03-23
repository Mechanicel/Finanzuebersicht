from __future__ import annotations

import uuid

from src.repositories.mongo_repository import MongoMarketDataRepository


def main() -> int:
    repo = MongoMarketDataRepository()
    repo.ping()

    isin = f"SMOKE-{uuid.uuid4()}"
    payload = {
        "isin": isin,
        "basic": {"companyName": "Smoke Inc."},
        "metrics": {"sharesOutstanding": 1000},
        "metrics_history": [{"date": "2025-12-31", "marketCap": 100000}],
        "etf": {},
    }

    repo.write(isin, payload)
    loaded = repo.read(isin)

    if not loaded or loaded.get("isin") != isin:
        raise RuntimeError("Smoke-Test fehlgeschlagen: Dokument konnte nicht persistiert werden")

    print(f"Mongo Smoke-Test erfolgreich für ISIN={isin}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
