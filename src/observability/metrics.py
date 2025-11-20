"""
CloudWatch metrics publishing.

This module provides a comprehensive metrics publishing system for tracking
application performance, API usage, errors, and resource counts.
"""

import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

from src.core.config import get_settings
from src.core.constants import MetricName, MetricUnit
from src.core.logging import get_logger

logger = get_logger(__name__)


class MetricsPublisher:
    """
    CloudWatch metrics publisher with batching and error handling.
    """

    def __init__(self, namespace: Optional[str] = None):
        """
        Initialize metrics publisher.

        Args:
            namespace: CloudWatch namespace (defaults to config value)
        """
        settings = get_settings()
        self.namespace = namespace or settings.cloudwatch_namespace
        self.enabled = settings.enable_metrics

        self._client = None
        self._metric_buffer: List[Dict[str, Any]] = []
        self._buffer_size = 20  # CloudWatch max is 20 metrics per request

        if self.enabled:
            try:
                session = boto3.Session(
                    profile_name=settings.aws_profile,
                    region_name=settings.aws_region,
                )
                self._client = session.client("cloudwatch")
                logger.info(f"CloudWatch metrics enabled in namespace: {self.namespace}")
            except Exception as e:
                logger.error(f"Failed to initialize CloudWatch client: {e}")
                self.enabled = False

    def put_metric(
        self,
        metric_name: str,
        value: float,
        unit: str = MetricUnit.COUNT,
        dimensions: Optional[Dict[str, str]] = None,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """
        Publish a single metric to CloudWatch.

        Args:
            metric_name: Metric name
            value: Metric value
            unit: Metric unit (Seconds, Milliseconds, Count, Percent, Bytes)
            dimensions: Metric dimensions as key-value pairs
            timestamp: Metric timestamp (defaults to now)
        """
        if not self.enabled:
            return

        metric_data = {
            "MetricName": metric_name,
            "Value": value,
            "Unit": unit,
            "Timestamp": timestamp or datetime.utcnow(),
        }

        if dimensions:
            metric_data["Dimensions"] = [
                {"Name": k, "Value": v} for k, v in dimensions.items()
            ]

        self._metric_buffer.append(metric_data)

        # Flush buffer if it reaches the size limit
        if len(self._metric_buffer) >= self._buffer_size:
            self.flush()

    def put_duration(
        self,
        metric_name: str,
        duration_seconds: float,
        dimensions: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Publish a duration metric in milliseconds.

        Args:
            metric_name: Metric name
            duration_seconds: Duration in seconds
            dimensions: Metric dimensions
        """
        self.put_metric(
            metric_name=metric_name,
            value=duration_seconds * 1000,  # Convert to milliseconds
            unit=MetricUnit.MILLISECONDS,
            dimensions=dimensions,
        )

    def put_count(
        self,
        metric_name: str,
        count: int,
        dimensions: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Publish a count metric.

        Args:
            metric_name: Metric name
            count: Count value
            dimensions: Metric dimensions
        """
        self.put_metric(
            metric_name=metric_name,
            value=float(count),
            unit=MetricUnit.COUNT,
            dimensions=dimensions,
        )

    def increment(
        self,
        metric_name: str,
        dimensions: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Increment a counter metric by 1.

        Args:
            metric_name: Metric name
            dimensions: Metric dimensions
        """
        self.put_count(metric_name, 1, dimensions)

    def record_resource_count(
        self,
        resource_type: str,
        count: int,
        region: Optional[str] = None,
    ) -> None:
        """
        Record the count of discovered resources.

        Args:
            resource_type: Type of AWS resource
            count: Number of resources discovered
            region: AWS region
        """
        dimensions = {"ResourceType": resource_type}
        if region:
            dimensions["Region"] = region

        self.put_count(
            metric_name=MetricName.RESOURCE_COUNT,
            count=count,
            dimensions=dimensions,
        )

    def record_api_call(
        self,
        api_name: str,
        success: bool,
        duration_seconds: Optional[float] = None,
        region: Optional[str] = None,
    ) -> None:
        """
        Record an AWS API call with success/failure status.

        Args:
            api_name: AWS API operation name (e.g., 'ec2:DescribeVpcs')
            success: Whether the API call succeeded
            duration_seconds: API call duration in seconds
            region: AWS region
        """
        dimensions = {"APIName": api_name}
        if region:
            dimensions["Region"] = region

        # Record success or failure count
        if success:
            self.increment(MetricName.API_CALL_SUCCESS, dimensions)
        else:
            self.increment(MetricName.API_CALL_FAILURE, dimensions)

        # Record total API call count
        self.increment(MetricName.API_CALL_COUNT, dimensions)

        # Record duration if provided
        if duration_seconds is not None:
            self.put_duration(
                metric_name=MetricName.COLLECTOR_DURATION,
                duration_seconds=duration_seconds,
                dimensions=dimensions,
            )

    def record_error(
        self,
        error_type: str,
        component: Optional[str] = None,
    ) -> None:
        """
        Record an error occurrence.

        Args:
            error_type: Type of error
            component: Component where error occurred
        """
        dimensions = {"ErrorType": error_type}
        if component:
            dimensions["Component"] = component

        self.increment(MetricName.ERROR_COUNT, dimensions)

    def record_anomaly(
        self,
        anomaly_type: str,
        severity: str,
        count: int = 1,
    ) -> None:
        """
        Record detected anomalies.

        Args:
            anomaly_type: Type of anomaly detected
            severity: Severity level (critical, high, medium, low)
            count: Number of anomalies detected
        """
        dimensions = {
            "AnomalyType": anomaly_type,
            "Severity": severity,
        }

        self.put_count(
            metric_name=MetricName.ANOMALY_COUNT,
            count=count,
            dimensions=dimensions,
        )

    def record_bedrock_usage(
        self,
        model_id: str,
        input_tokens: int,
        output_tokens: int,
    ) -> None:
        """
        Record Bedrock token usage.

        Args:
            model_id: Bedrock model ID
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
        """
        dimensions = {"ModelId": model_id, "TokenType": "Input"}
        self.put_count(
            metric_name=MetricName.BEDROCK_TOKEN_USAGE,
            count=input_tokens,
            dimensions=dimensions,
        )

        dimensions["TokenType"] = "Output"
        self.put_count(
            metric_name=MetricName.BEDROCK_TOKEN_USAGE,
            count=output_tokens,
            dimensions=dimensions,
        )

    def flush(self) -> None:
        """
        Flush buffered metrics to CloudWatch.
        """
        if not self.enabled or not self._metric_buffer:
            return

        if not self._client:
            logger.warning("CloudWatch client not initialized, cannot flush metrics")
            self._metric_buffer.clear()
            return

        try:
            # Split buffer into chunks of max size
            for i in range(0, len(self._metric_buffer), self._buffer_size):
                chunk = self._metric_buffer[i : i + self._buffer_size]

                self._client.put_metric_data(
                    Namespace=self.namespace,
                    MetricData=chunk,
                )

            logger.debug(f"Flushed {len(self._metric_buffer)} metrics to CloudWatch")
            self._metric_buffer.clear()

        except ClientError as e:
            logger.error(f"Failed to publish metrics to CloudWatch: {e}")
            self._metric_buffer.clear()
        except Exception as e:
            logger.error(f"Unexpected error publishing metrics: {e}")
            self._metric_buffer.clear()

    def __del__(self):
        """Flush remaining metrics on deletion."""
        self.flush()


class MetricsTimer:
    """
    Context manager for timing operations and publishing metrics.

    Example:
        with MetricsTimer(metrics, MetricName.DISCOVERY_DURATION, {"Region": "us-east-1"}):
            # Perform discovery operation
            pass
    """

    def __init__(
        self,
        publisher: MetricsPublisher,
        metric_name: str,
        dimensions: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize metrics timer.

        Args:
            publisher: Metrics publisher instance
            metric_name: Name of the metric to record
            dimensions: Metric dimensions
        """
        self.publisher = publisher
        self.metric_name = metric_name
        self.dimensions = dimensions
        self.start_time = None

    def __enter__(self):
        """Start the timer."""
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop the timer and publish the metric."""
        if self.start_time is not None:
            duration = time.time() - self.start_time
            self.publisher.put_duration(
                metric_name=self.metric_name,
                duration_seconds=duration,
                dimensions=self.dimensions,
            )


# Global metrics publisher instance
_metrics_publisher: Optional[MetricsPublisher] = None


def get_metrics_publisher() -> MetricsPublisher:
    """
    Get the global metrics publisher instance.

    Returns:
        MetricsPublisher instance
    """
    global _metrics_publisher
    if _metrics_publisher is None:
        _metrics_publisher = MetricsPublisher()
    return _metrics_publisher
