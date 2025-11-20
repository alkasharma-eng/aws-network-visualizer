"""
Rate limiting utilities for AWS API calls.

This module provides rate limiters to ensure we stay within AWS API limits
and implement graceful throttling.
"""

import asyncio
import time
from collections import deque
from typing import Optional

from src.core.logging import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """
    Token bucket rate limiter for synchronous operations.

    This implementation uses a token bucket algorithm to ensure operations
    stay within specified rate limits.
    """

    def __init__(self, rate: float, burst: Optional[int] = None):
        """
        Initialize rate limiter.

        Args:
            rate: Maximum operations per second
            burst: Maximum burst size (defaults to rate)
        """
        self.rate = rate
        self.burst = burst or int(rate)
        self.tokens = float(self.burst)
        self.last_update = time.time()
        self._lock = None  # Use threading.Lock if needed

    def acquire(self, tokens: int = 1, blocking: bool = True) -> bool:
        """
        Acquire tokens from the bucket.

        Args:
            tokens: Number of tokens to acquire
            blocking: If True, wait until tokens are available

        Returns:
            True if tokens were acquired, False otherwise
        """
        while True:
            # Refill tokens based on elapsed time
            now = time.time()
            elapsed = now - self.last_update
            self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
            self.last_update = now

            # Check if enough tokens available
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True

            if not blocking:
                return False

            # Calculate wait time for next token
            deficit = tokens - self.tokens
            wait_time = deficit / self.rate
            time.sleep(wait_time)

    def __enter__(self):
        """Context manager entry."""
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        pass


class AsyncRateLimiter:
    """
    Token bucket rate limiter for asynchronous operations.
    """

    def __init__(self, rate: float, burst: Optional[int] = None):
        """
        Initialize async rate limiter.

        Args:
            rate: Maximum operations per second
            burst: Maximum burst size (defaults to rate)
        """
        self.rate = rate
        self.burst = burst or int(rate)
        self.tokens = float(self.burst)
        self.last_update = time.time()
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1, blocking: bool = True) -> bool:
        """
        Acquire tokens from the bucket asynchronously.

        Args:
            tokens: Number of tokens to acquire
            blocking: If True, wait until tokens are available

        Returns:
            True if tokens were acquired, False otherwise
        """
        async with self._lock:
            while True:
                # Refill tokens based on elapsed time
                now = time.time()
                elapsed = now - self.last_update
                self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
                self.last_update = now

                # Check if enough tokens available
                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return True

                if not blocking:
                    return False

                # Calculate wait time for next token
                deficit = tokens - self.tokens
                wait_time = deficit / self.rate

        # Wait outside the lock to allow other coroutines
        await asyncio.sleep(wait_time)

    async def __aenter__(self):
        """Async context manager entry."""
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        pass


class SlidingWindowRateLimiter:
    """
    Sliding window rate limiter that tracks requests in a time window.

    This is useful for enforcing strict rate limits like "100 requests per minute".
    """

    def __init__(self, max_requests: int, window_seconds: float):
        """
        Initialize sliding window rate limiter.

        Args:
            max_requests: Maximum requests allowed in the window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = deque()

    def acquire(self, blocking: bool = True) -> bool:
        """
        Acquire permission to make a request.

        Args:
            blocking: If True, wait until capacity is available

        Returns:
            True if permission granted, False otherwise
        """
        while True:
            now = time.time()

            # Remove requests outside the window
            while self.requests and self.requests[0] < now - self.window_seconds:
                self.requests.popleft()

            # Check if we have capacity
            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                return True

            if not blocking:
                return False

            # Wait until the oldest request expires
            if self.requests:
                wait_time = self.window_seconds - (now - self.requests[0])
                if wait_time > 0:
                    time.sleep(wait_time)

    def __enter__(self):
        """Context manager entry."""
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        pass


class AsyncSlidingWindowRateLimiter:
    """
    Async sliding window rate limiter.
    """

    def __init__(self, max_requests: int, window_seconds: float):
        """
        Initialize async sliding window rate limiter.

        Args:
            max_requests: Maximum requests allowed in the window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = deque()
        self._lock = asyncio.Lock()

    async def acquire(self, blocking: bool = True) -> bool:
        """
        Acquire permission to make a request asynchronously.

        Args:
            blocking: If True, wait until capacity is available

        Returns:
            True if permission granted, False otherwise
        """
        async with self._lock:
            while True:
                now = time.time()

                # Remove requests outside the window
                while self.requests and self.requests[0] < now - self.window_seconds:
                    self.requests.popleft()

                # Check if we have capacity
                if len(self.requests) < self.max_requests:
                    self.requests.append(now)
                    return True

                if not blocking:
                    return False

                # Calculate wait time
                if self.requests:
                    wait_time = self.window_seconds - (now - self.requests[0])
                    if wait_time > 0:
                        # Release lock while waiting
                        pass
                    else:
                        continue

        # Wait outside the lock
        if wait_time > 0:
            await asyncio.sleep(wait_time)

    async def __aenter__(self):
        """Async context manager entry."""
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        pass
