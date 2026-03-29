from __future__ import annotations

from functools import lru_cache

from app.data import PERSON_SNAPSHOT_DATA
from app.service import AnalyticsService


@lru_cache(maxsize=1)
def get_analytics_service() -> AnalyticsService:
    return AnalyticsService(PERSON_SNAPSHOT_DATA)
