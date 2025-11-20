"""
Structured logging setup with CloudWatch integration.

This module provides comprehensive logging capabilities with structured JSON output,
CloudWatch Logs integration, and correlation with AWS X-Ray traces.
"""

import logging
import sys
import uuid
from contextvars import ContextVar
from typing import Any, Dict, Optional

from pythonjsonlogger import jsonlogger

from src.core.config import get_settings

# Context variables for request tracking
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
trace_id_var: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom JSON formatter that includes request context and standardized fields.
    """

    def add_fields(
        self,
        log_record: Dict[str, Any],
        record: logging.LogRecord,
        message_dict: Dict[str, Any],
    ) -> None:
        """
        Add custom fields to the log record.

        Args:
            log_record: Dictionary to be logged as JSON
            record: Original log record
            message_dict: Message dictionary
        """
        super().add_fields(log_record, record, message_dict)

        # Add standard fields
        log_record["timestamp"] = self.formatTime(record, self.datefmt)
        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        log_record["module"] = record.module
        log_record["function"] = record.funcName
        log_record["line"] = record.lineno

        # Add application context
        settings = get_settings()
        log_record["service"] = settings.app_name
        log_record["version"] = settings.app_version
        log_record["environment"] = settings.environment

        # Add request context
        request_id = request_id_var.get()
        if request_id:
            log_record["request_id"] = request_id

        trace_id = trace_id_var.get()
        if trace_id:
            log_record["trace_id"] = trace_id

        # Add exception info if present
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        # Add any extra fields
        if hasattr(record, "extra_fields"):
            log_record.update(record.extra_fields)


def setup_logging(
    log_level: Optional[str] = None,
    enable_structured: Optional[bool] = None,
    enable_cloudwatch: bool = False,
) -> logging.Logger:
    """
    Set up application logging with structured JSON output.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        enable_structured: Enable structured JSON logging
        enable_cloudwatch: Enable CloudWatch Logs handler

    Returns:
        Configured root logger
    """
    settings = get_settings()

    # Use settings if not provided
    if log_level is None:
        log_level = settings.log_level
    if enable_structured is None:
        enable_structured = settings.enable_structured_logging

    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Remove existing handlers
    logger.handlers = []

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    if enable_structured:
        # Use JSON formatter for structured logging
        formatter = CustomJsonFormatter(
            "%(timestamp)s %(level)s %(name)s %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S.%fZ",
        )
    else:
        # Use standard formatter for development
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Add CloudWatch handler if enabled
    if enable_cloudwatch:
        try:
            import watchtower

            cloudwatch_handler = watchtower.CloudWatchLogHandler(
                log_group=settings.cloudwatch_log_group,
                stream_name=f"{settings.app_name}-{settings.environment}",
                use_queues=True,
            )
            cloudwatch_handler.setLevel(log_level)
            cloudwatch_handler.setFormatter(formatter)
            logger.addHandler(cloudwatch_handler)
        except ImportError:
            logger.warning(
                "watchtower not installed, CloudWatch logging disabled. "
                "Install with: pip install watchtower"
            )
        except Exception as e:
            logger.error(f"Failed to set up CloudWatch logging: {e}")

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.

    Args:
        name: Module name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def set_request_id(request_id: Optional[str] = None) -> str:
    """
    Set request ID for current context.

    Args:
        request_id: Request ID to set, or None to generate new one

    Returns:
        The request ID that was set
    """
    if request_id is None:
        request_id = str(uuid.uuid4())
    request_id_var.set(request_id)
    return request_id


def get_request_id() -> Optional[str]:
    """
    Get request ID for current context.

    Returns:
        Current request ID or None
    """
    return request_id_var.get()


def set_trace_id(trace_id: str) -> None:
    """
    Set AWS X-Ray trace ID for current context.

    Args:
        trace_id: X-Ray trace ID
    """
    trace_id_var.set(trace_id)


def get_trace_id() -> Optional[str]:
    """
    Get AWS X-Ray trace ID for current context.

    Returns:
        Current trace ID or None
    """
    return trace_id_var.get()


def log_with_context(
    logger: logging.Logger,
    level: int,
    message: str,
    **extra_fields: Any,
) -> None:
    """
    Log a message with additional context fields.

    Args:
        logger: Logger instance
        level: Log level
        message: Log message
        **extra_fields: Additional fields to include in structured log
    """
    # Create a log record with extra fields
    extra = {"extra_fields": extra_fields}
    logger.log(level, message, extra=extra)


class LogContext:
    """
    Context manager for adding temporary context to logs.

    Example:
        with LogContext(user_id="123", action="create"):
            logger.info("Creating resource")
    """

    def __init__(self, **context: Any):
        """
        Initialize log context.

        Args:
            **context: Context fields to add to logs
        """
        self.context = context
        self.old_factory = None

    def __enter__(self):
        """Enter the context."""
        old_factory = logging.getLogRecordFactory()
        self.old_factory = old_factory

        def record_factory(*args, **kwargs):
            record = old_factory(*args, **kwargs)
            if not hasattr(record, "extra_fields"):
                record.extra_fields = {}
            record.extra_fields.update(self.context)
            return record

        logging.setLogRecordFactory(record_factory)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context."""
        if self.old_factory:
            logging.setLogRecordFactory(self.old_factory)


# Initialize logging on module import
setup_logging()
