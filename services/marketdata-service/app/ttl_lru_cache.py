from __future__ import annotations

from collections import OrderedDict
from datetime import UTC, datetime, timedelta
from threading import Lock
from typing import Any


class TtlLruCache:
    def __init__(self, *, max_size: int, ttl_seconds: float) -> None:
        self._max_size = max(1, max_size)
        self._ttl = timedelta(seconds=max(0.0, ttl_seconds))
        self._entries: OrderedDict[Any, tuple[Any, datetime]] = OrderedDict()
        self._lock = Lock()

    def get(self, key: Any) -> Any | None:
        now = datetime.now(UTC)
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return None
            value, expires_at = entry
            if now >= expires_at:
                self._entries.pop(key, None)
                return None
            self._entries.move_to_end(key)
            return value

    def set(self, key: Any, value: Any) -> None:
        expires_at = datetime.now(UTC) + self._ttl
        with self._lock:
            self._entries[key] = (value, expires_at)
            self._entries.move_to_end(key)
            while len(self._entries) > self._max_size:
                self._entries.popitem(last=False)

    def delete(self, key: Any) -> None:
        with self._lock:
            self._entries.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()
