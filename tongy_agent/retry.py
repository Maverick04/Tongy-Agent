"""
Retry mechanism for LLM API calls.

Provides exponential backoff retry logic for handling transient failures.
"""

import asyncio
import logging
from functools import wraps
from typing import Any, Callable, TypeVar

from tongy_agent.schema.schema import RetryConfig

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RetryError(Exception):
    """Raised when all retry attempts are exhausted."""

    def __init__(self, message: str, attempts: int, last_exception: Exception | None = None):
        super().__init__(message)
        self.attempts = attempts
        self.last_exception = last_exception


def async_retry(config: RetryConfig) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator for async functions with retry logic.

    Args:
        config: Retry configuration

    Returns:
        Decorated function with retry logic
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            if not config.enabled:
                return await func(*args, **kwargs)

            last_exception: Exception | None = None

            for attempt in range(config.max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    is_last_attempt = attempt == config.max_retries - 1

                    if is_last_attempt:
                        logger.error(
                            f"Function {func.__name__} failed after {config.max_retries} attempts: {e}"
                        )
                        raise RetryError(
                            f"Failed after {config.max_retries} attempts",
                            attempts=config.max_retries,
                            last_exception=e,
                        ) from e

                    delay = config.get_delay(attempt)
                    logger.warning(
                        f"Function {func.__name__} failed (attempt {attempt + 1}/{config.max_retries}): {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    await asyncio.sleep(delay)

            # This should never be reached, but for type safety
            raise RetryError(
                "Unexpected retry failure",
                attempts=config.max_retries,
                last_exception=last_exception,
            )

        return wrapper

    return decorator


def sync_retry(config: RetryConfig) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator for synchronous functions with retry logic.

    Args:
        config: Retry configuration

    Returns:
        Decorated function with retry logic
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            if not config.enabled:
                return func(*args, **kwargs)

            last_exception: Exception | None = None

            for attempt in range(config.max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    is_last_attempt = attempt == config.max_retries - 1

                    if is_last_attempt:
                        logger.error(
                            f"Function {func.__name__} failed after {config.max_retries} attempts: {e}"
                        )
                        raise RetryError(
                            f"Failed after {config.max_retries} attempts",
                            attempts=config.max_retries,
                            last_exception=e,
                        ) from e

                    delay = config.get_delay(attempt)
                    logger.warning(
                        f"Function {func.__name__} failed (attempt {attempt + 1}/{config.max_retries}): {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    import time

                    time.sleep(delay)

            # This should never be reached, but for type safety
            raise RetryError(
                "Unexpected retry failure",
                attempts=config.max_retries,
                last_exception=last_exception,
            )

        return wrapper

    return decorator
