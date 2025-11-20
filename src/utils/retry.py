"""
Retry logic with exponential backoff for AWS API calls.

This module provides decorators and utilities for handling transient failures
with configurable retry strategies.
"""

import asyncio
import functools
import time
from typing import Any, Callable, Optional, Tuple, Type, TypeVar, cast

from botocore.exceptions import ClientError

from src.core.config import get_settings
from src.core.exceptions import RetryExhausted, RateLimitException
from src.core.logging import get_logger

logger = get_logger(__name__)

# Type variable for function signatures
F = TypeVar("F", bound=Callable[..., Any])

# Retriable error codes
RETRIABLE_ERROR_CODES = {
    "RequestLimitExceeded",
    "Throttling",
    "ThrottlingException",
    "TooManyRequestsException",
    "ProvisionedThroughputExceededException",
    "RequestThrottledException",
    "ServiceUnavailable",
    "InternalError",
    "InternalFailure",
}


def is_retriable_error(error: Exception) -> bool:
    """
    Check if an error should be retried.

    Args:
        error: Exception to check

    Returns:
        True if error should be retried
    """
    if isinstance(error, ClientError):
        error_code = error.response.get("Error", {}).get("Code", "")
        return error_code in RETRIABLE_ERROR_CODES
    return False


def calculate_backoff_delay(
    attempt: int,
    base_delay: float,
    max_delay: float,
    jitter: bool = True,
) -> float:
    """
    Calculate exponential backoff delay with optional jitter.

    Args:
        attempt: Current attempt number (0-indexed)
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        jitter: Whether to add random jitter

    Returns:
        Delay in seconds
    """
    import random

    # Calculate exponential backoff: base_delay * 2^attempt
    delay = min(base_delay * (2**attempt), max_delay)

    # Add jitter to prevent thundering herd
    if jitter:
        delay = delay * (0.5 + random.random() * 0.5)

    return delay


def retry_with_backoff(
    max_attempts: Optional[int] = None,
    base_delay: Optional[float] = None,
    max_delay: Optional[float] = None,
    retriable_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
) -> Callable[[F], F]:
    """
    Decorator to retry a synchronous function with exponential backoff.

    Args:
        max_attempts: Maximum retry attempts (defaults to config value)
        base_delay: Base delay for backoff in seconds (defaults to config value)
        max_delay: Maximum delay in seconds
        retriable_exceptions: Tuple of exception types to retry on

    Returns:
        Decorated function

    Example:
        @retry_with_backoff(max_attempts=3, base_delay=1.0)
        def describe_vpcs(ec2_client):
            return ec2_client.describe_vpcs()
    """
    settings = get_settings()

    # Use config values if not provided
    if max_attempts is None:
        max_attempts = settings.max_retry_attempts
    if base_delay is None:
        base_delay = settings.retry_base_delay
    if max_delay is None:
        max_delay = 60.0
    if retriable_exceptions is None:
        retriable_exceptions = (ClientError,)

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)

                except retriable_exceptions as e:
                    last_exception = e

                    # Check if this is a retriable error
                    if not is_retriable_error(e):
                        logger.warning(
                            f"{func.__name__} failed with non-retriable error: {e}",
                            extra={"error_type": type(e).__name__},
                        )
                        raise

                    # Check if this is a rate limit error
                    if isinstance(e, ClientError):
                        error_code = e.response.get("Error", {}).get("Code", "")
                        if error_code in ["RequestLimitExceeded", "Throttling"]:
                            raise RateLimitException(
                                f"Rate limited on {func.__name__}",
                                details={"error": str(e)},
                            )

                    # Don't retry on last attempt
                    if attempt == max_attempts - 1:
                        break

                    # Calculate backoff delay
                    delay = calculate_backoff_delay(attempt, base_delay, max_delay)

                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt + 1}/{max_attempts}), "
                        f"retrying in {delay:.2f}s: {e}",
                        extra={
                            "function": func.__name__,
                            "attempt": attempt + 1,
                            "max_attempts": max_attempts,
                            "delay": delay,
                            "error": str(e),
                        },
                    )

                    time.sleep(delay)

            # All retries exhausted
            raise RetryExhausted(
                f"Failed after {max_attempts} attempts: {last_exception}",
                attempts=max_attempts,
                details={"last_error": str(last_exception)},
            )

        return cast(F, wrapper)

    return decorator


def async_retry_with_backoff(
    max_attempts: Optional[int] = None,
    base_delay: Optional[float] = None,
    max_delay: Optional[float] = None,
    retriable_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
) -> Callable[[F], F]:
    """
    Decorator to retry an asynchronous function with exponential backoff.

    Args:
        max_attempts: Maximum retry attempts (defaults to config value)
        base_delay: Base delay for backoff in seconds (defaults to config value)
        max_delay: Maximum delay in seconds
        retriable_exceptions: Tuple of exception types to retry on

    Returns:
        Decorated async function

    Example:
        @async_retry_with_backoff(max_attempts=3, base_delay=1.0)
        async def describe_vpcs_async(ec2_client):
            return await ec2_client.describe_vpcs()
    """
    settings = get_settings()

    # Use config values if not provided
    if max_attempts is None:
        max_attempts = settings.max_retry_attempts
    if base_delay is None:
        base_delay = settings.retry_base_delay
    if max_delay is None:
        max_delay = 60.0
    if retriable_exceptions is None:
        retriable_exceptions = (ClientError,)

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)

                except retriable_exceptions as e:
                    last_exception = e

                    # Check if this is a retriable error
                    if not is_retriable_error(e):
                        logger.warning(
                            f"{func.__name__} failed with non-retriable error: {e}",
                            extra={"error_type": type(e).__name__},
                        )
                        raise

                    # Check if this is a rate limit error
                    if isinstance(e, ClientError):
                        error_code = e.response.get("Error", {}).get("Code", "")
                        if error_code in ["RequestLimitExceeded", "Throttling"]:
                            raise RateLimitException(
                                f"Rate limited on {func.__name__}",
                                details={"error": str(e)},
                            )

                    # Don't retry on last attempt
                    if attempt == max_attempts - 1:
                        break

                    # Calculate backoff delay
                    delay = calculate_backoff_delay(attempt, base_delay, max_delay)

                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt + 1}/{max_attempts}), "
                        f"retrying in {delay:.2f}s: {e}",
                        extra={
                            "function": func.__name__,
                            "attempt": attempt + 1,
                            "max_attempts": max_attempts,
                            "delay": delay,
                            "error": str(e),
                        },
                    )

                    await asyncio.sleep(delay)

            # All retries exhausted
            raise RetryExhausted(
                f"Failed after {max_attempts} attempts: {last_exception}",
                attempts=max_attempts,
                details={"last_error": str(last_exception)},
            )

        return cast(F, wrapper)

    return decorator
