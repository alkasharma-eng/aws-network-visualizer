"""
Custom exceptions for AWS Network Visualizer.

This module defines a hierarchy of custom exceptions to provide clear error
handling and reporting throughout the application.
"""

from typing import Any, Dict, Optional


class NetworkVisualizerException(Exception):
    """Base exception for all AWS Network Visualizer errors."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the exception.

        Args:
            message: Human-readable error message
            error_code: Machine-readable error code for categorization
            details: Additional context about the error
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "UNKNOWN_ERROR"
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for structured logging."""
        return {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
        }


class CollectorException(NetworkVisualizerException):
    """Exception raised during AWS resource collection."""

    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize collector exception.

        Args:
            message: Error message
            resource_type: Type of AWS resource being collected
            resource_id: ID of the specific resource that failed
            **kwargs: Additional details
        """
        details = kwargs.pop("details", {})
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id
        super().__init__(message, error_code="COLLECTOR_ERROR", details=details)


class StorageException(NetworkVisualizerException):
    """Exception raised during storage operations."""

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        storage_type: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize storage exception.

        Args:
            message: Error message
            operation: Storage operation that failed (read, write, delete)
            storage_type: Type of storage (dynamodb, s3, cache)
            **kwargs: Additional details
        """
        details = kwargs.pop("details", {})
        if operation:
            details["operation"] = operation
        if storage_type:
            details["storage_type"] = storage_type
        super().__init__(message, error_code="STORAGE_ERROR", details=details)


class VisualizationException(NetworkVisualizerException):
    """Exception raised during visualization generation."""

    def __init__(
        self,
        message: str,
        visualization_type: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize visualization exception.

        Args:
            message: Error message
            visualization_type: Type of visualization (png, svg, html)
            **kwargs: Additional details
        """
        details = kwargs.pop("details", {})
        if visualization_type:
            details["visualization_type"] = visualization_type
        super().__init__(message, error_code="VISUALIZATION_ERROR", details=details)


class AIAnalysisException(NetworkVisualizerException):
    """Exception raised during AI-powered analysis."""

    def __init__(
        self,
        message: str,
        analysis_type: Optional[str] = None,
        model_id: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize AI analysis exception.

        Args:
            message: Error message
            analysis_type: Type of analysis being performed
            model_id: Bedrock model ID being used
            **kwargs: Additional details
        """
        details = kwargs.pop("details", {})
        if analysis_type:
            details["analysis_type"] = analysis_type
        if model_id:
            details["model_id"] = model_id
        super().__init__(message, error_code="AI_ANALYSIS_ERROR", details=details)


class ConfigurationException(NetworkVisualizerException):
    """Exception raised for configuration errors."""

    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize configuration exception.

        Args:
            message: Error message
            config_key: Configuration key that caused the error
            **kwargs: Additional details
        """
        details = kwargs.pop("details", {})
        if config_key:
            details["config_key"] = config_key
        super().__init__(message, error_code="CONFIGURATION_ERROR", details=details)


class RetryExhausted(CollectorException):
    """Exception raised when retry attempts are exhausted."""

    def __init__(
        self,
        message: str,
        attempts: int,
        **kwargs,
    ):
        """
        Initialize retry exhausted exception.

        Args:
            message: Error message
            attempts: Number of retry attempts made
            **kwargs: Additional details
        """
        details = kwargs.pop("details", {})
        details["retry_attempts"] = attempts
        super().__init__(message, **kwargs)
        self.error_code = "RETRY_EXHAUSTED"


class RateLimitException(CollectorException):
    """Exception raised when AWS API rate limits are hit."""

    def __init__(
        self,
        message: str,
        service: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize rate limit exception.

        Args:
            message: Error message
            service: AWS service that rate limited the request
            **kwargs: Additional details
        """
        details = kwargs.pop("details", {})
        if service:
            details["service"] = service
        super().__init__(message, **kwargs)
        self.error_code = "RATE_LIMIT_ERROR"
