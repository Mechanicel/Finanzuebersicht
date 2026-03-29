from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Generic, TypeVar

T = TypeVar("T")


class CacheEntry(Generic[T]):
    def __init__(self, value: T, expires_at: datetime) -> None:
        self.value = value
        self.expires_at = expires_at


class TTLMemoryCache(Generic[T]):
    def __init__(self, ttl_seconds: int) -> None:
        self.ttl_seconds = ttl_seconds
        self._store: dict[str, CacheEntry[T]] = {}

    def get(self, key: str) -> T | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        if datetime.now(UTC) >= entry.expires_at:
            self._store.pop(key, None)
            return None
        return entry.value

    def set(self, key: str, value: T) -> None:
        self._store[key] = CacheEntry(
            value=value,
            expires_at=datetime.now(UTC) + timedelta(seconds=self.ttl_seconds),
        )
