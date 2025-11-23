"""
Load Balancer collector.

Collects Application Load Balancers (ALB), Network Load Balancers (NLB),
Gateway Load Balancers (GLB), and Classic Load Balancers (CLB) for
comprehensive enterprise application architecture visualization.
"""

from typing import Any, Dict, List, Optional

from src.collectors.base import BaseCollector
from src.core.constants import ResourceType
from src.core.logging import get_logger

logger = get_logger(__name__)


class LoadBalancerCollector(BaseCollector):
    """
    Collector for AWS Load Balancer resources (ALB, NLB, GLB, CLB).

    Load balancers distribute incoming application traffic across multiple
    targets. Critical for high-availability enterprise applications.
    """

    def __init__(
        self,
        region: str,
        profile: Optional[str] = None,
        rate_limit: Optional[float] = None,
        vpc_id: Optional[str] = None,
    ):
        """
        Initialize Load Balancer collector.

        Args:
            region: AWS region
            profile: AWS profile
            rate_limit: Rate limit in requests/second
            vpc_id: Optional VPC ID to filter load balancers
        """
        super().__init__(region, profile, rate_limit)
        self.vpc_id = vpc_id

    @property
    def resource_type(self) -> ResourceType:
        """Resource type for this collector."""
        return ResourceType.LOAD_BALANCER

    @property
    def service_name(self) -> str:
        """AWS service name."""
        return "elbv2"

    async def collect_resources(self) -> List[Dict[str, Any]]:
        """
        Collect Load Balancer resources.

        Returns:
            List of load balancer dictionaries with normalized structure

        Raises:
            CollectorException: If collection fails
        """
        all_lbs = []

        # Collect ALB/NLB/GLB (ELBv2)
        elbv2_lbs = await self._collect_elbv2()
        all_lbs.extend(elbv2_lbs)

        # Collect Classic Load Balancers (ELB)
        classic_lbs = await self._collect_classic()
        all_lbs.extend(classic_lbs)

        logger.info(
            f"Collected {len(all_lbs)} Load Balancers ({len(elbv2_lbs)} ELBv2, {len(classic_lbs)} Classic) in {self.region}",
            extra={
                "total_count": len(all_lbs),
                "elbv2_count": len(elbv2_lbs),
                "classic_count": len(classic_lbs),
                "region": self.region,
            },
        )

        return all_lbs

    async def _collect_elbv2(self) -> List[Dict[str, Any]]:
        """
        Collect ELBv2 load balancers (ALB, NLB, GLB).

        Returns:
            List of normalized load balancer dictionaries
        """
        client = self.get_client("elbv2")

        # Collect load balancers with pagination
        load_balancers = await self._paginated_call(
            client=client,
            method_name="describe_load_balancers",
            result_key="LoadBalancers",
        )

        # Filter by VPC if specified
        if self.vpc_id:
            load_balancers = [lb for lb in load_balancers if lb.get("VpcId") == self.vpc_id]

        # Collect tags for all load balancers (batch operation)
        lb_arns = [lb["LoadBalancerArn"] for lb in load_balancers]
        tags_by_arn = {}

        if lb_arns:
            # Batch tag collection (max 20 ARNs per request)
            batch_size = 20
            for i in range(0, len(lb_arns), batch_size):
                batch_arns = lb_arns[i : i + batch_size]
                tags_response = await self._simple_call(
                    client=client,
                    method_name="describe_tags",
                    ResourceArns=batch_arns,
                )
                for tag_desc in tags_response.get("TagDescriptions", []):
                    arn = tag_desc.get("ResourceArn")
                    tags_by_arn[arn] = tag_desc.get("Tags", [])

        # Normalize load balancer data
        normalized_lbs = []
        for lb in load_balancers:
            lb_arn = lb["LoadBalancerArn"]
            availability_zones = lb.get("AvailabilityZones", [])

            # Collect target groups for this load balancer
            try:
                tg_response = await self._simple_call(
                    client=client,
                    method_name="describe_target_groups",
                    LoadBalancerArn=lb_arn,
                )
                target_groups = tg_response.get("TargetGroups", [])
            except Exception as e:
                logger.warning(f"Could not collect target groups for {lb_arn}: {e}")
                target_groups = []

            normalized_lb = {
                "id": lb_arn,
                "name": lb.get("LoadBalancerName"),
                "dns_name": lb.get("DNSName"),
                "canonical_hosted_zone_id": lb.get("CanonicalHostedZoneId"),
                "created_time": lb.get("CreatedTime").isoformat() if lb.get("CreatedTime") else None,
                "load_balancer_type": lb.get("Type"),  # application, network, gateway
                "scheme": lb.get("Scheme"),  # internet-facing or internal
                "vpc_id": lb.get("VpcId"),
                "state": lb.get("State", {}).get("Code"),
                "ip_address_type": lb.get("IpAddressType"),  # ipv4 or dualstack
                # Network configuration
                "availability_zones": [
                    {
                        "zone_name": az.get("ZoneName"),
                        "zone_id": az.get("ZoneId"),
                        "subnet_id": az.get("SubnetId"),
                        "outpost_id": az.get("OutpostId"),
                        "load_balancer_addresses": az.get("LoadBalancerAddresses", []),
                    }
                    for az in availability_zones
                ],
                "subnet_ids": [az.get("SubnetId") for az in availability_zones],
                "security_groups": lb.get("SecurityGroups", []),
                # Target groups
                "target_groups": [
                    {
                        "target_group_arn": tg.get("TargetGroupArn"),
                        "target_group_name": tg.get("TargetGroupName"),
                        "protocol": tg.get("Protocol"),
                        "port": tg.get("Port"),
                        "vpc_id": tg.get("VpcId"),
                        "health_check_protocol": tg.get("HealthCheckProtocol"),
                        "health_check_port": tg.get("HealthCheckPort"),
                        "health_check_enabled": tg.get("HealthCheckEnabled"),
                        "health_check_interval_seconds": tg.get("HealthCheckIntervalSeconds"),
                        "health_check_timeout_seconds": tg.get("HealthCheckTimeoutSeconds"),
                        "healthy_threshold_count": tg.get("HealthyThresholdCount"),
                        "unhealthy_threshold_count": tg.get("UnhealthyThresholdCount"),
                        "target_type": tg.get("TargetType"),  # instance, ip, lambda, alb
                    }
                    for tg in target_groups
                ],
                # Customer-managed key
                "customer_owned_ipv4_pool": lb.get("CustomerOwnedIpv4Pool"),
                # Tags
                "tags": self._extract_elbv2_tags(tags_by_arn.get(lb_arn, [])),
                "name_tag": self._get_name_from_elbv2_tags(tags_by_arn.get(lb_arn, [])),
                "region": self.region,
                "resource_type": self.resource_type.value,
                "lb_version": "v2",
                # Enhanced metadata for enterprise analysis
                "is_internet_facing": lb.get("Scheme") == "internet-facing",
                "is_active": lb.get("State", {}).get("Code") == "active",
                "zone_count": len(availability_zones),
                "target_group_count": len(target_groups),
                "security_group_count": len(lb.get("SecurityGroups", [])),
                "raw": lb,
            }
            normalized_lbs.append(normalized_lb)

        return normalized_lbs

    async def _collect_classic(self) -> List[Dict[str, Any]]:
        """
        Collect Classic Load Balancers (ELB).

        Returns:
            List of normalized load balancer dictionaries
        """
        client = self.get_client("elb")

        # Collect classic load balancers
        try:
            classic_lbs = await self._paginated_call(
                client=client,
                method_name="describe_load_balancers",
                result_key="LoadBalancerDescriptions",
            )
        except Exception as e:
            logger.warning(f"Could not collect Classic Load Balancers: {e}")
            return []

        # Filter by VPC if specified
        if self.vpc_id:
            classic_lbs = [lb for lb in classic_lbs if lb.get("VPCId") == self.vpc_id]

        # Collect tags for all classic load balancers
        lb_names = [lb["LoadBalancerName"] for lb in classic_lbs]
        tags_by_name = {}

        if lb_names:
            # Batch tag collection (max 20 names per request)
            batch_size = 20
            for i in range(0, len(lb_names), batch_size):
                batch_names = lb_names[i : i + batch_size]
                try:
                    tags_response = await self._simple_call(
                        client=client,
                        method_name="describe_tags",
                        LoadBalancerNames=batch_names,
                    )
                    for tag_desc in tags_response.get("TagDescriptions", []):
                        name = tag_desc.get("LoadBalancerName")
                        tags_by_name[name] = tag_desc.get("Tags", [])
                except Exception as e:
                    logger.warning(f"Could not collect tags for classic LBs: {e}")

        # Normalize classic load balancer data
        normalized_lbs = []
        for lb in classic_lbs:
            lb_name = lb["LoadBalancerName"]

            normalized_lb = {
                "id": lb_name,
                "name": lb_name,
                "dns_name": lb.get("DNSName"),
                "canonical_hosted_zone_id": lb.get("CanonicalHostedZoneNameID"),
                "created_time": lb.get("CreatedTime").isoformat() if lb.get("CreatedTime") else None,
                "load_balancer_type": "classic",
                "scheme": lb.get("Scheme"),
                "vpc_id": lb.get("VPCId"),
                "subnet_ids": lb.get("Subnets", []),
                "availability_zones": [{"zone_name": az} for az in lb.get("AvailabilityZones", [])],
                "security_groups": lb.get("SecurityGroups", []),
                "instances": [inst.get("InstanceId") for inst in lb.get("Instances", [])],
                "health_check": lb.get("HealthCheck", {}),
                "listener_descriptions": lb.get("ListenerDescriptions", []),
                "source_security_group": lb.get("SourceSecurityGroup", {}),
                # Tags
                "tags": self._extract_elbv2_tags(tags_by_name.get(lb_name, [])),
                "name_tag": self._get_name_from_elbv2_tags(tags_by_name.get(lb_name, [])),
                "region": self.region,
                "resource_type": self.resource_type.value,
                "lb_version": "classic",
                # Enhanced metadata
                "is_internet_facing": lb.get("Scheme") == "internet-facing",
                "is_active": True,  # Classic LBs don't have state
                "zone_count": len(lb.get("AvailabilityZones", [])),
                "instance_count": len(lb.get("Instances", [])),
                "security_group_count": len(lb.get("SecurityGroups", [])),
                "raw": lb,
            }
            normalized_lbs.append(normalized_lb)

        return normalized_lbs

    def _extract_elbv2_tags(self, tags: List[Dict[str, str]]) -> Dict[str, str]:
        """Extract ELBv2 tags into a dictionary."""
        if not tags:
            return {}
        return {tag.get("Key", ""): tag.get("Value", "") for tag in tags}

    def _get_name_from_elbv2_tags(self, tags: List[Dict[str, str]]) -> str:
        """Get the Name tag value from ELBv2 tags."""
        if not tags:
            return ""
        for tag in tags:
            if tag.get("Key") == "Name":
                return tag.get("Value", "")
        return ""
