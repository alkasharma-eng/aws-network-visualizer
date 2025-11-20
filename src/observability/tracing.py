"""
AWS X-Ray distributed tracing integration.

This module provides decorators and utilities for comprehensive distributed tracing
across all AWS API calls and application components.
"""

import functools
import time
from typing import Any, Callable, Dict, Optional, TypeVar, cast

from src.core.config import get_settings
from src.core.logging import get_logger, set_trace_id

logger = get_logger(__name__)

# Type variable for function signatures
F = TypeVar("F", bound=Callable[..., Any])


class TracerStub:
    """
    Stub tracer for when X-Ray is disabled.
    Provides no-op implementations of tracing methods.
    """

    def begin_segment(self, name: str) -> "SegmentStub":
        """Begin a new segment (no-op)."""
        return SegmentStub()

    def begin_subsegment(self, name: str) -> "SegmentStub":
        """Begin a new subsegment (no-op)."""
        return SegmentStub()

    def current_segment(self) -> "SegmentStub":
        """Get current segment (no-op)."""
        return SegmentStub()


class SegmentStub:
    """
    Stub segment for when X-Ray is disabled.
    Provides no-op implementations of segment methods.
    """

    def __enter__(self):
        """Enter context (no-op)."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context (no-op)."""
        pass

    def put_annotation(self, key: str, value: Any) -> None:
        """Add annotation (no-op)."""
        pass

    def put_metadata(self, key: str, value: Any, namespace: str = "default") -> None:
        """Add metadata (no-op)."""
        pass

    def set_user(self, user: str) -> None:
        """Set user (no-op)."""
        pass


class Tracer:
    """
    Wrapper around AWS X-Ray tracer with fallback to stub.
    """

    def __init__(self):
        """Initialize the tracer."""
        settings = get_settings()
        self.enabled = settings.enable_xray
        self._xray = None

        if self.enabled:
            try:
                from aws_xray_sdk.core import xray_recorder
                from aws_xray_sdk.core import patch_all

                # Patch all supported libraries
                patch_all()

                self._xray = xray_recorder
                self._xray.configure(
                    service=settings.app_name,
                    context_missing="LOG_ERROR",
                )
                logger.info("AWS X-Ray tracing enabled")
            except ImportError:
                logger.warning(
                    "aws-xray-sdk not installed, tracing disabled. "
                    "Install with: pip install aws-xray-sdk"
                )
                self.enabled = False
            except Exception as e:
                logger.error(f"Failed to initialize X-Ray: {e}")
                self.enabled = False

    def begin_segment(self, name: str):
        """
        Begin a new segment.

        Args:
            name: Segment name

        Returns:
            Segment context manager
        """
        if self.enabled and self._xray:
            segment = self._xray.begin_segment(name)
            # Update trace ID in logging context
            if hasattr(segment, "trace_id"):
                set_trace_id(segment.trace_id)
            return segment
        return SegmentStub()

    def begin_subsegment(self, name: str):
        """
        Begin a new subsegment.

        Args:
            name: Subsegment name

        Returns:
            Subsegment context manager
        """
        if self.enabled and self._xray:
            return self._xray.begin_subsegment(name)
        return SegmentStub()

    def current_segment(self):
        """
        Get the current segment.

        Returns:
            Current segment or stub
        """
        if self.enabled and self._xray:
            try:
                return self._xray.current_segment()
            except Exception:
                return SegmentStub()
        return SegmentStub()

    def capture(self, name: Optional[str] = None):
        """
        Decorator to capture a function as a subsegment.

        Args:
            name: Subsegment name (defaults to function name)

        Returns:
            Decorated function
        """
        if self.enabled and self._xray:
            return self._xray.capture(name)

        # Return pass-through decorator if tracing disabled
        def decorator(func: F) -> F:
            return func

        return decorator


# Global tracer instance
_tracer: Optional[Tracer] = None


def get_tracer() -> Tracer:
    """
    Get the global tracer instance.

    Returns:
        Tracer instance
    """
    global _tracer
    if _tracer is None:
        _tracer = Tracer()
    return _tracer


def trace_function(
    name: Optional[str] = None,
    capture_args: bool = False,
    capture_result: bool = False,
) -> Callable[[F], F]:
    """
    Decorator to trace a synchronous function with X-Ray.

    Args:
        name: Subsegment name (defaults to function name)
        capture_args: Whether to capture function arguments as metadata
        capture_result: Whether to capture function result as metadata

    Returns:
        Decorated function

    Example:
        @trace_function(name="collect_vpcs", capture_args=True)
        def collect_vpcs(region: str) -> List[Dict]:
            # Function implementation
            pass
    """

    def decorator(func: F) -> F:
        subsegment_name = name or func.__name__

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = get_tracer()
            start_time = time.time()

            with tracer.begin_subsegment(subsegment_name) as subsegment:
                try:
                    # Add function metadata
                    subsegment.put_annotation("function", func.__name__)
                    subsegment.put_annotation("module", func.__module__)

                    # Capture arguments if requested
                    if capture_args:
                        try:
                            subsegment.put_metadata(
                                "arguments",
                                {"args": str(args), "kwargs": str(kwargs)},
                                namespace="function",
                            )
                        except Exception as e:
                            logger.warning(f"Failed to capture args: {e}")

                    # Execute function
                    result = func(*args, **kwargs)

                    # Capture result if requested
                    if capture_result:
                        try:
                            subsegment.put_metadata(
                                "result", str(result), namespace="function"
                            )
                        except Exception as e:
                            logger.warning(f"Failed to capture result: {e}")

                    # Add success annotation
                    subsegment.put_annotation("status", "success")

                    return result

                except Exception as e:
                    # Add error metadata
                    subsegment.put_annotation("status", "error")
                    subsegment.put_annotation("error_type", type(e).__name__)
                    subsegment.put_metadata(
                        "error",
                        {"message": str(e), "type": type(e).__name__},
                        namespace="function",
                    )
                    raise

                finally:
                    # Add duration
                    duration = time.time() - start_time
                    subsegment.put_annotation("duration_ms", int(duration * 1000))

        return cast(F, wrapper)

    return decorator


def trace_async_function(
    name: Optional[str] = None,
    capture_args: bool = False,
    capture_result: bool = False,
) -> Callable[[F], F]:
    """
    Decorator to trace an asynchronous function with X-Ray.

    Args:
        name: Subsegment name (defaults to function name)
        capture_args: Whether to capture function arguments as metadata
        capture_result: Whether to capture function result as metadata

    Returns:
        Decorated async function

    Example:
        @trace_async_function(name="collect_vpcs_async", capture_args=True)
        async def collect_vpcs_async(region: str) -> List[Dict]:
            # Async function implementation
            pass
    """

    def decorator(func: F) -> F:
        subsegment_name = name or func.__name__

        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = get_tracer()
            start_time = time.time()

            with tracer.begin_subsegment(subsegment_name) as subsegment:
                try:
                    # Add function metadata
                    subsegment.put_annotation("function", func.__name__)
                    subsegment.put_annotation("module", func.__module__)
                    subsegment.put_annotation("is_async", True)

                    # Capture arguments if requested
                    if capture_args:
                        try:
                            subsegment.put_metadata(
                                "arguments",
                                {"args": str(args), "kwargs": str(kwargs)},
                                namespace="function",
                            )
                        except Exception as e:
                            logger.warning(f"Failed to capture args: {e}")

                    # Execute async function
                    result = await func(*args, **kwargs)

                    # Capture result if requested
                    if capture_result:
                        try:
                            subsegment.put_metadata(
                                "result", str(result), namespace="function"
                            )
                        except Exception as e:
                            logger.warning(f"Failed to capture result: {e}")

                    # Add success annotation
                    subsegment.put_annotation("status", "success")

                    return result

                except Exception as e:
                    # Add error metadata
                    subsegment.put_annotation("status", "error")
                    subsegment.put_annotation("error_type", type(e).__name__)
                    subsegment.put_metadata(
                        "error",
                        {"message": str(e), "type": type(e).__name__},
                        namespace="function",
                    )
                    raise

                finally:
                    # Add duration
                    duration = time.time() - start_time
                    subsegment.put_annotation("duration_ms", int(duration * 1000))

        return cast(F, wrapper)

    return decorator
