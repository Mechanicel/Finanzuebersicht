from __future__ import annotations

import logging
import time
from enum import Enum
from threading import Lock

LOGGER = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"      # normal operation
    OPEN = "open"          # rejecting calls fast
    HALF_OPEN = "half_open"  # one probe allowed


class CircuitOpenError(Exception):
    """Raised when a circuit is open and a call is attempted."""

    def __init__(self, service_name: str) -> None:
        super().__init__(f"Circuit open for '{service_name}' — service temporarily unavailable")
        self.service_name = service_name


class CircuitBreaker:
    """
    Simple three-state circuit breaker (CLOSED → OPEN → HALF_OPEN → CLOSED).

    CLOSED  : normal operation; failure_count tracks consecutive errors.
    OPEN    : all calls rejected immediately after failure_threshold errors.
    HALF_OPEN: one probe is allowed after recovery_timeout_seconds; success
               resets to CLOSED, failure returns to OPEN.
    """

    def __init__(
        self,
        service_name: str,
        failure_threshold: int = 5,
        recovery_timeout_seconds: float = 30.0,
    ) -> None:
        self._service_name = service_name
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout_seconds
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: float | None = None
        self._lock = Lock()

    @property
    def state(self) -> CircuitState:
        with self._lock:
            return self._current_state()

    @property
    def service_name(self) -> str:
        return self._service_name

    def _current_state(self) -> CircuitState:
        """Must be called with self._lock held."""
        if (
            self._state == CircuitState.OPEN
            and self._last_failure_time is not None
            and time.monotonic() - self._last_failure_time >= self._recovery_timeout
        ):
            self._state = CircuitState.HALF_OPEN
            LOGGER.info("circuit_breaker state=half_open service=%s", self._service_name)
        return self._state

    def is_open(self) -> bool:
        """Returns True when the circuit should reject the call."""
        return self.state == CircuitState.OPEN

    def before_call(self) -> None:
        """
        Call this before making an upstream request.
        Raises CircuitOpenError if the circuit is open.
        """
        with self._lock:
            state = self._current_state()
            if state == CircuitState.OPEN:
                raise CircuitOpenError(self._service_name)

    def record_success(self) -> None:
        with self._lock:
            if self._state != CircuitState.CLOSED:
                LOGGER.info(
                    "circuit_breaker state=closed service=%s (recovered after %s failures)",
                    self._service_name,
                    self._failure_count,
                )
            self._failure_count = 0
            self._state = CircuitState.CLOSED

    def record_failure(self) -> None:
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.monotonic()
            if self._failure_count >= self._failure_threshold:
                if self._state != CircuitState.OPEN:
                    LOGGER.warning(
                        "circuit_breaker state=open service=%s failure_count=%d",
                        self._service_name,
                        self._failure_count,
                    )
                self._state = CircuitState.OPEN
