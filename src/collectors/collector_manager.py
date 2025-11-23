"""
Collector manager for orchestrating multiple resource collectors.

This module coordinates the collection of resources across multiple collectors
with parallel execution and comprehensive error handling.
"""

import asyncio
from typing import Dict, List, Optional, Type

from src.collectors.base import BaseCollector, CollectorResult
from src.collectors.vpc_collector import VPCCollector
from src.collectors.subnet_collector import SubnetCollector
from src.collectors.ec2_collector import EC2Collector
from src.collectors.igw_collector import InternetGatewayCollector
from src.collectors.security_group_collector import SecurityGroupCollector
from src.collectors.nat_gateway_collector import NATGatewayCollector
from src.collectors.route_table_collector import RouteTableCollector
from src.collectors.network_acl_collector import NetworkACLCollector
from src.collectors.transit_gateway_collector import TransitGatewayCollector
from src.collectors.vpc_peering_collector import VPCPeeringCollector
from src.collectors.vpn_connection_collector import VPNConnectionCollector
from src.collectors.direct_connect_collector import DirectConnectCollector
from src.collectors.load_balancer_collector import LoadBalancerCollector
from src.collectors.rds_collector import RDSCollector
from src.collectors.lambda_eni_collector import LambdaENICollector
from src.core.config import get_settings
from src.core.constants import ResourceType
from src.core.logging import get_logger
from src.observability.metrics import get_metrics_publisher, MetricsTimer
from src.observability.tracing import get_tracer

logger = get_logger(__name__)


class CollectorManager:
    """
    Manages and orchestrates multiple resource collectors.
    """

    # Map of resource types to collector classes
    COLLECTOR_CLASSES: Dict[ResourceType, Type[BaseCollector]] = {
        ResourceType.VPC: VPCCollector,
        ResourceType.SUBNET: SubnetCollector,
        ResourceType.EC2_INSTANCE: EC2Collector,
        ResourceType.INTERNET_GATEWAY: InternetGatewayCollector,
        ResourceType.SECURITY_GROUP: SecurityGroupCollector,
        ResourceType.NAT_GATEWAY: NATGatewayCollector,
        ResourceType.ROUTE_TABLE: RouteTableCollector,
        ResourceType.NETWORK_ACL: NetworkACLCollector,
        ResourceType.TRANSIT_GATEWAY: TransitGatewayCollector,
        ResourceType.VPC_PEERING: VPCPeeringCollector,
        ResourceType.VPN_CONNECTION: VPNConnectionCollector,
        ResourceType.DIRECT_CONNECT: DirectConnectCollector,
        ResourceType.LOAD_BALANCER: LoadBalancerCollector,
        ResourceType.RDS_INSTANCE: RDSCollector,
        ResourceType.LAMBDA_ENI: LambdaENICollector,
    }

    def __init__(
        self,
        regions: Optional[List[str]] = None,
        profile: Optional[str] = None,
        max_concurrent: Optional[int] = None,
    ):
        """
        Initialize collector manager.

        Args:
            regions: List of AWS regions to collect from
            profile: AWS CLI profile name
            max_concurrent: Maximum concurrent collectors
        """
        self.settings = get_settings()
        self.regions = regions or self.settings.aws_regions
        self.profile = profile or self.settings.aws_profile
        self.max_concurrent = max_concurrent or self.settings.max_concurrent_collectors

        self.metrics = get_metrics_publisher()
        self.tracer = get_tracer()

        logger.info(
            f"Initialized CollectorManager for {len(self.regions)} regions",
            extra={
                "regions": self.regions,
                "max_concurrent": self.max_concurrent,
            },
        )

    def get_enabled_resource_types(self) -> List[ResourceType]:
        """
        Get list of resource types enabled in configuration.

        Returns:
            List of enabled ResourceType values
        """
        enabled = []

        if self.settings.collect_vpcs:
            enabled.append(ResourceType.VPC)
        if self.settings.collect_subnets:
            enabled.append(ResourceType.SUBNET)
        if self.settings.collect_ec2_instances:
            enabled.append(ResourceType.EC2_INSTANCE)
        if self.settings.collect_internet_gateways:
            enabled.append(ResourceType.INTERNET_GATEWAY)
        if self.settings.collect_security_groups:
            enabled.append(ResourceType.SECURITY_GROUP)
        if self.settings.collect_nat_gateways:
            enabled.append(ResourceType.NAT_GATEWAY)
        if self.settings.collect_route_tables:
            enabled.append(ResourceType.ROUTE_TABLE)
        if self.settings.collect_network_acls:
            enabled.append(ResourceType.NETWORK_ACL)
        if self.settings.collect_transit_gateways:
            enabled.append(ResourceType.TRANSIT_GATEWAY)
        if self.settings.collect_vpc_peering:
            enabled.append(ResourceType.VPC_PEERING)
        if self.settings.collect_vpn_connections:
            enabled.append(ResourceType.VPN_CONNECTION)
        if self.settings.collect_direct_connect:
            enabled.append(ResourceType.DIRECT_CONNECT)
        if self.settings.collect_load_balancers:
            enabled.append(ResourceType.LOAD_BALANCER)
        if self.settings.collect_rds_instances:
            enabled.append(ResourceType.RDS_INSTANCE)
        if self.settings.collect_lambda_enis:
            enabled.append(ResourceType.LAMBDA_ENI)

        return enabled

    async def collect_all(
        self,
        resource_types: Optional[List[ResourceType]] = None,
    ) -> Dict[str, List[CollectorResult]]:
        """
        Collect all enabled resources across all regions.

        Args:
            resource_types: Optional list of specific resource types to collect

        Returns:
            Dictionary mapping regions to list of CollectorResults

        Raises:
            CollectorException: If critical collection errors occur
        """
        if resource_types is None:
            resource_types = self.get_enabled_resource_types()

        logger.info(
            f"Starting collection of {len(resource_types)} resource types across {len(self.regions)} regions",
            extra={
                "resource_types": [rt.value for rt in resource_types],
                "regions": self.regions,
            },
        )

        with MetricsTimer(self.metrics, "total_discovery_duration"):
            with self.tracer.begin_subsegment("collect_all_resources"):
                # Create collector tasks for all regions and resource types
                tasks = []
                for region in self.regions:
                    for resource_type in resource_types:
                        if resource_type in self.COLLECTOR_CLASSES:
                            tasks.append(
                                self._collect_resource_type(region, resource_type)
                            )

                # Execute tasks with concurrency limit
                results = await self._execute_with_limit(tasks, self.max_concurrent)

        # Organize results by region
        results_by_region: Dict[str, List[CollectorResult]] = {}
        successful_count = 0
        failed_count = 0

        for result in results:
            if result:
                region = result.region
                if region not in results_by_region:
                    results_by_region[region] = []
                results_by_region[region].append(result)

                if result.success:
                    successful_count += 1
                else:
                    failed_count += 1

        logger.info(
            f"Collection completed: {successful_count} successful, {failed_count} failed",
            extra={
                "successful": successful_count,
                "failed": failed_count,
                "total_regions": len(results_by_region),
            },
        )

        return results_by_region

    async def collect_region(
        self,
        region: str,
        resource_types: Optional[List[ResourceType]] = None,
    ) -> List[CollectorResult]:
        """
        Collect resources for a single region.

        Args:
            region: AWS region
            resource_types: Optional list of specific resource types to collect

        Returns:
            List of CollectorResults
        """
        if resource_types is None:
            resource_types = self.get_enabled_resource_types()

        logger.info(
            f"Collecting {len(resource_types)} resource types in {region}",
            extra={"region": region, "resource_types": [rt.value for rt in resource_types]},
        )

        tasks = [
            self._collect_resource_type(region, resource_type)
            for resource_type in resource_types
            if resource_type in self.COLLECTOR_CLASSES
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and None values
        return [r for r in results if isinstance(r, CollectorResult)]

    async def _collect_resource_type(
        self,
        region: str,
        resource_type: ResourceType,
    ) -> Optional[CollectorResult]:
        """
        Collect a specific resource type in a region.

        Args:
            region: AWS region
            resource_type: Resource type to collect

        Returns:
            CollectorResult or None if failed
        """
        collector_class = self.COLLECTOR_CLASSES.get(resource_type)
        if not collector_class:
            logger.warning(
                f"No collector class found for {resource_type.value}",
                extra={"resource_type": resource_type.value},
            )
            return None

        try:
            collector = collector_class(region=region, profile=self.profile)
            result = await collector.collect()
            return result

        except Exception as e:
            logger.error(
                f"Failed to collect {resource_type.value} in {region}: {e}",
                extra={
                    "region": region,
                    "resource_type": resource_type.value,
                    "error": str(e),
                },
                exc_info=True,
            )
            self.metrics.record_error(
                error_type=type(e).__name__,
                component="CollectorManager",
            )
            return None

    async def _execute_with_limit(
        self,
        tasks: List,
        max_concurrent: int,
    ) -> List:
        """
        Execute tasks with concurrency limit.

        Args:
            tasks: List of coroutines to execute
            max_concurrent: Maximum concurrent tasks

        Returns:
            List of results
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def bounded_task(task):
            async with semaphore:
                return await task

        bounded_tasks = [bounded_task(task) for task in tasks]
        return await asyncio.gather(*bounded_tasks, return_exceptions=True)

    def get_summary(self, results: Dict[str, List[CollectorResult]]) -> Dict:
        """
        Generate a summary of collection results.

        Args:
            results: Dictionary of results by region

        Returns:
            Summary dictionary
        """
        total_resources = 0
        resources_by_type = {}
        resources_by_region = {}

        for region, region_results in results.items():
            region_count = 0

            for result in region_results:
                total_resources += result.count
                region_count += result.count

                # Count by type
                rt = result.resource_type.value
                if rt not in resources_by_type:
                    resources_by_type[rt] = 0
                resources_by_type[rt] += result.count

            resources_by_region[region] = region_count

        return {
            "total_resources": total_resources,
            "total_regions": len(results),
            "resources_by_type": resources_by_type,
            "resources_by_region": resources_by_region,
        }
