"""
Retry policies and circuit breaker configuration for PitchPilot.

Provides reusable retry decorators and circuit breakers for
external service calls (OpenAI, Tavily, Supabase, Redis).
"""

from __future__ import annotations

import functools
import logging
from typing import Any, Callable, TypeVar

from circuitbreaker import CircuitBreaker, CircuitBreakerError
from tenacity import (
    RetryCallState,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


# ── Retry Logging ─────────────────────────────────────────────────

def _log_retry_attempt(retry_state: RetryCallState) -> None:
    """Log retry attempts with context."""
    exception = retry_state.outcome.exception() if retry_state.outcome else None
    logger.warning(
        "Retry attempt %d/%s for %s: %s",
        retry_state.attempt_number,
        retry_state.retry_object.stop.max_attempt_number  # type: ignore[attr-defined]
        if hasattr(retry_state.retry_object, "stop")
        else "?",
        retry_state.fn.__name__ if retry_state.fn else "unknown",
        str(exception) if exception else "no exception",
        extra={
            "attempt": retry_state.attempt_number,
            "function": retry_state.fn.__name__ if retry_state.fn else "unknown",
            "error": str(exception) if exception else None,
        },
    )


# ── LLM Retry Policy ─────────────────────────────────────────────

llm_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type((Exception,)),
    before_sleep=_log_retry_attempt,
    reraise=True,
)
"""
Retry decorator for LLM API calls.

- 3 attempts max
- Exponential backoff: 2s, 4s, 8s (capped at 30s)
- Retries on any exception (OpenAI errors, timeouts, network issues)
"""


# ── Database Retry Policy ────────────────────────────────────────

db_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.5, min=1, max=10),
    retry=retry_if_exception_type((ConnectionError, TimeoutError, OSError)),
    before_sleep=_log_retry_attempt,
    reraise=True,
)
"""
Retry decorator for database operations.

- 3 attempts max
- Exponential backoff: 1s, 2s, 4s (capped at 10s)
- Retries on connection/timeout errors only
"""


# ── External Service Retry Policy ────────────────────────────────

external_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=15),
    retry=retry_if_exception_type((ConnectionError, TimeoutError, Exception)),
    before_sleep=_log_retry_attempt,
    reraise=True,
)
"""
Retry decorator for external service calls (Tavily, Supabase Storage, etc).

- 3 attempts max
- Exponential backoff: 1s, 2s, 4s (capped at 15s)
"""


# ── Circuit Breakers ─────────────────────────────────────────────

class LoggingCircuitBreaker(CircuitBreaker):
    """Circuit breaker that logs state transitions."""

    def __init__(
        self,
        fail_max: int = 5,
        reset_timeout: int = 60,
        name: str = "unknown",
        **kwargs: Any,
    ) -> None:
        super().__init__(
            fail_max=fail_max,
            reset_timeout=reset_timeout,
            **kwargs,
        )
        self._breaker_name = name

    def on_open(self) -> None:
        """Called when circuit breaker opens (too many failures)."""
        logger.error(
            "Circuit breaker OPEN: %s (failures: %d)",
            self._breaker_name,
            self.fail_counter,
            extra={"circuit_breaker": self._breaker_name, "state": "open"},
        )

    def on_close(self) -> None:
        """Called when circuit breaker closes (service recovered)."""
        logger.info(
            "Circuit breaker CLOSED: %s (recovered)",
            self._breaker_name,
            extra={"circuit_breaker": self._breaker_name, "state": "closed"},
        )

    def on_half_open(self) -> None:
        """Called when circuit breaker enters half-open state."""
        logger.info(
            "Circuit breaker HALF-OPEN: %s (testing recovery)",
            self._breaker_name,
            extra={"circuit_breaker": self._breaker_name, "state": "half_open"},
        )


# Pre-configured circuit breakers for each external service
openai_breaker = LoggingCircuitBreaker(
    fail_max=5, reset_timeout=60, name="openai"
)

tavily_breaker = LoggingCircuitBreaker(
    fail_max=3, reset_timeout=30, name="tavily"
)

supabase_breaker = LoggingCircuitBreaker(
    fail_max=5, reset_timeout=45, name="supabase"
)

redis_breaker = LoggingCircuitBreaker(
    fail_max=5, reset_timeout=30, name="redis"
)


def with_circuit_breaker(breaker: CircuitBreaker) -> Callable[[F], F]:
    """
    Decorator to wrap a function with a circuit breaker.

    Usage:
        @with_circuit_breaker(openai_breaker)
        async def call_openai(...):
            ...
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await breaker.call_async(func, *args, **kwargs)
            except CircuitBreakerError:
                logger.error(
                    "Circuit breaker is OPEN for %s — request rejected",
                    func.__name__,
                )
                raise
        return wrapper  # type: ignore[return-value]
    return decorator
