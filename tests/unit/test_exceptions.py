"""
Unit tests for exception module.
"""

import pytest

from src.core.exceptions import (
    NetworkVisualizerException,
    CollectorException,
    StorageException,
    VisualizationException,
    AIAnalysisException,
    RetryExhausted,
    RateLimitException,
)


class TestExceptions:
    """Test custom exceptions."""

    def test_base_exception(self):
        """Test base exception."""
        exc = NetworkVisualizerException(
            "Test error",
            error_code="TEST_ERROR",
            details={"key": "value"},
        )

        assert str(exc) == "Test error"
        assert exc.error_code == "TEST_ERROR"
        assert exc.details == {"key": "value"}

        exc_dict = exc.to_dict()
        assert exc_dict["error_type"] == "NetworkVisualizerException"
        assert exc_dict["message"] == "Test error"

    def test_collector_exception(self):
        """Test collector exception."""
        exc = CollectorException(
            "Collection failed",
            resource_type="vpc",
            resource_id="vpc-123",
        )

        assert "vpc" in exc.details["resource_type"]
        assert "vpc-123" in exc.details["resource_id"]

    def test_storage_exception(self):
        """Test storage exception."""
        exc = StorageException(
            "Storage failed",
            operation="write",
            storage_type="dynamodb",
        )

        assert exc.details["operation"] == "write"
        assert exc.details["storage_type"] == "dynamodb"

    def test_retry_exhausted(self):
        """Test retry exhausted exception."""
        exc = RetryExhausted("Retries exhausted", attempts=3)

        assert exc.details["retry_attempts"] == 3
        assert exc.error_code == "RETRY_EXHAUSTED"

    def test_rate_limit_exception(self):
        """Test rate limit exception."""
        exc = RateLimitException("Rate limited", service="ec2")

        assert exc.details["service"] == "ec2"
        assert exc.error_code == "RATE_LIMIT_ERROR"
