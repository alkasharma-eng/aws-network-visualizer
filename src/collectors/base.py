"""
Base collector class with common functionality.

This module provides the base collector class that all resource collectors
inherit from, including retry logic, metrics, tracing, and error handling.
"""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

from src.core.config import get_settings
from src.core.constants import ResourceType
from src.core.exceptions import CollectorException
from src.core.logging import get_logger
from src.observability.metrics import get_metrics_publisher, MetricsTimer
from src.observability.tracing import trace_async_function, get_tracer
from src.utils.retry import async_retry_with_backoff
from src.utils.rate_limiter import AsyncRateLimiter

logger = get_logger(__name__)


@dataclass
class CollectorResult:
    """
    Result from a resource collection operation.
    """

    resource_type: ResourceType
    region: str
    resources: List[Dict[str, Any]] = field(default_factory=list)
    count: int = 0
    duration_seconds: float = 0.0
    success: bool = True
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Update count if not set."""
        if self.count == 0 and self.resources:
            self.count = len(self.resources)


class BaseCollector(ABC):
    """
    Base class for all AWS resource collectors.

    Provides common functionality for:
    - AWS session management
    - Retry logic with exponential backoff
    - Rate limiting
    - CloudWatch metrics
    - AWS X-Ray tracing
    - Error handling
    """

    def __init__(
        self,
        region: str,
        profile: Optional[str] = None,
        rate_limit: Optional[float] = None,
    ):
        """
        Initialize the base collector.

        Args:
            region: AWS region to collect from
            profile: AWS CLI profile name
            rate_limit: Rate limit in requests per second
        """
        self.region = region
        self.settings = get_settings()
        self.metrics = get_metrics_publisher()
        self.tracer = get_tracer()

        # Create AWS session
        self.session = boto3.Session(
            profile_name=profile or self.settings.aws_profile,
            region_name=region,
        )

        # Set up rate limiter if specified
        self.rate_limiter = None
        if rate_limit:
            self.rate_limiter = AsyncRateLimiter(rate=rate_limit)

        logger.info(
            f"Initialized {self.__class__.__name__} for region {region}",
            extra={"region": region, "collector": self.__class__.__name__},
        )

    @property
    @abstractmethod
    def resource_type(self) -> ResourceType:
        """
        Resource type handled by this collector.

        Returns:
            ResourceType enum value
        """
        pass

    @property
    @abstractmethod
    def service_name(self) -> str:
        """
        AWS service name (e.g., 'ec2', 'elbv2').

        Returns:
            Service name
        """
        pass

    def get_client(self, service: Optional[str] = None):
        """
        Get AWS service client.

        Args:
            service: Service name (defaults to self.service_name)

        Returns:
            Boto3 client
        """
        return self.session.client(
            service or self.service_name,
            config=boto3.session.Config(
                connect_timeout=self.settings.api_call_timeout,
                read_timeout=self.settings.api_call_timeout,
            ),
        )

    @abstractmethod
    async def collect_resources(self) -> List[Dict[str, Any]]:
        """
        Collect AWS resources.

        This method must be implemented by subclasses.

        Returns:
            List of resource dictionaries

        Raises:
            CollectorException: If collection fails
        """
        pass

    @trace_async_function(capture_args=False, capture_result=False)
    async def collect(self) -> CollectorResult:
        """
        Collect resources with full observability.

        Returns:
            CollectorResult with resources and metadata

        Raises:
            CollectorException: If collection fails after retries
        """
        start_time = time.time()
        result = CollectorResult(
            resource_type=self.resource_type,
            region=self.region,
        )

        try:
            logger.info(
                f"Starting collection of {self.resource_type.value} in {self.region}",
                extra={
                    "resource_type": self.resource_type.value,
                    "region": self.region,
                },
            )

            # Apply rate limiting if configured
            if self.rate_limiter:
                await self.rate_limiter.acquire()

            # Collect resources with metrics timing
            with MetricsTimer(
                self.metrics,
                f"{self.resource_type.value}_collection_duration",
                {"Region": self.region},
            ):
                resources = await self.collect_resources()

            result.resources = resources
            result.count = len(resources)
            result.success = True

            logger.info(
                f"Collected {result.count} {self.resource_type.value} resources in {self.region}",
                extra={
                    "resource_type": self.resource_type.value,
                    "region": self.region,
                    "count": result.count,
                },
            )

            # Record metrics
            self.metrics.record_resource_count(
                resource_type=self.resource_type.value,
                count=result.count,
                region=self.region,
            )

        except CollectorException as e:
            result.success = False
            result.error = str(e)
            logger.error(
                f"Collection failed for {self.resource_type.value} in {self.region}: {e}",
                extra={
                    "resource_type": self.resource_type.value,
                    "region": self.region,
                    "error": str(e),
                },
                exc_info=True,
            )

            # Record error metrics
            self.metrics.record_error(
                error_type=type(e).__name__,
                component=self.__class__.__name__,
            )

            raise

        except Exception as e:
            result.success = False
            result.error = str(e)
            logger.error(
                f"Unexpected error collecting {self.resource_type.value} in {self.region}: {e}",
                extra={
                    "resource_type": self.resource_type.value,
                    "region": self.region,
                    "error": str(e),
                },
                exc_info=True,
            )

            # Record error metrics
            self.metrics.record_error(
                error_type="UnexpectedError",
                component=self.__class__.__name__,
            )

            raise CollectorException(
                f"Failed to collect {self.resource_type.value}: {e}",
                resource_type=self.resource_type.value,
            )

        finally:
            result.duration_seconds = time.time() - start_time
            result.metadata["collector_class"] = self.__class__.__name__
            result.metadata["collection_time"] = time.time()

        return result

    @async_retry_with_backoff()
    async def _paginated_call(
        self,
        client,
        method_name: str,
        result_key: str,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """
        Make a paginated AWS API call with retry logic.

        Args:
            client: Boto3 client
            method_name: API method name (e.g., 'describe_vpcs')
            result_key: Key in response containing results (e.g., 'Vpcs')
            **kwargs: Additional arguments to pass to the API call

        Returns:
            List of resources from all pages

        Raises:
            CollectorException: If API call fails
        """
        api_name = f"{self.service_name}:{method_name}"
        start_time = time.time()

        try:
            method = getattr(client, method_name)
            paginator = client.get_paginator(method_name)

            all_resources = []
            page_count = 0

            for page in paginator.paginate(**kwargs):
                resources = page.get(result_key, [])
                all_resources.extend(resources)
                page_count += 1

            duration = time.time() - start_time

            # Record successful API call
            self.metrics.record_api_call(
                api_name=api_name,
                success=True,
                duration_seconds=duration,
                region=self.region,
            )

            logger.debug(
                f"{api_name} succeeded: {len(all_resources)} resources across {page_count} pages",
                extra={
                    "api_name": api_name,
                    "region": self.region,
                    "count": len(all_resources),
                    "pages": page_count,
                    "duration": duration,
                },
            )

            return all_resources

        except ClientError as e:
            duration = time.time() - start_time

            # Record failed API call
            self.metrics.record_api_call(
                api_name=api_name,
                success=False,
                duration_seconds=duration,
                region=self.region,
            )

            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            logger.error(
                f"{api_name} failed: {error_code} - {e}",
                extra={
                    "api_name": api_name,
                    "region": self.region,
                    "error_code": error_code,
                    "duration": duration,
                },
            )

            raise CollectorException(
                f"AWS API call failed: {e}",
                resource_type=self.resource_type.value,
                details={"api_name": api_name, "error_code": error_code},
            )

    async def _simple_call(
        self,
        client,
        method_name: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Make a simple (non-paginated) AWS API call with retry logic.

        Args:
            client: Boto3 client
            method_name: API method name
            **kwargs: Additional arguments

        Returns:
            API response

        Raises:
            CollectorException: If API call fails
        """
        api_name = f"{self.service_name}:{method_name}"
        start_time = time.time()

        try:
            method = getattr(client, method_name)
            response = method(**kwargs)

            duration = time.time() - start_time

            # Record successful API call
            self.metrics.record_api_call(
                api_name=api_name,
                success=True,
                duration_seconds=duration,
                region=self.region,
            )

            return response

        except ClientError as e:
            duration = time.time() - start_time

            # Record failed API call
            self.metrics.record_api_call(
                api_name=api_name,
                success=False,
                duration_seconds=duration,
                region=self.region,
            )

            raise CollectorException(
                f"AWS API call failed: {e}",
                resource_type=self.resource_type.value,
            )
