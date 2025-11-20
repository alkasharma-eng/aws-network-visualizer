"""
Subnet resource collector.
"""

from typing import Any, Dict, List, Optional

from src.collectors.base import BaseCollector
from src.core.constants import ResourceType
from src.core.logging import get_logger

logger = get_logger(__name__)


class SubnetCollector(BaseCollector):
    """
    Collector for AWS Subnet resources.
    """

    def __init__(
        self,
        region: str,
        profile: Optional[str] = None,
        rate_limit: Optional[float] = None,
        vpc_id: Optional[str] = None,
    ):
        """
        Initialize subnet collector.

        Args:
            region: AWS region
            profile: AWS profile
            rate_limit: Rate limit in requests/second
            vpc_id: Optional VPC ID to filter subnets
        """
        super().__init__(region, profile, rate_limit)
        self.vpc_id = vpc_id

    @property
    def resource_type(self) -> ResourceType:
        """Resource type for this collector."""
        return ResourceType.SUBNET

    @property
    def service_name(self) -> str:
        """AWS service name."""
        return "ec2"

    async def collect_resources(self) -> List[Dict[str, Any]]:
        """
        Collect Subnet resources.

        Returns:
            List of Subnet dictionaries with normalized structure

        Raises:
            CollectorException: If collection fails
        """
        client = self.get_client()

        # Build filters
        filters = []
        if self.vpc_id:
            filters.append({"Name": "vpc-id", "Values": [self.vpc_id]})

        # Collect subnets with pagination
        kwargs = {}
        if filters:
            kwargs["Filters"] = filters

        subnets = await self._paginated_call(
            client=client,
            method_name="describe_subnets",
            result_key="Subnets",
            **kwargs,
        )

        # Normalize subnet data
        normalized_subnets = []
        for subnet in subnets:
            normalized_subnet = {
                "id": subnet["SubnetId"],
                "vpc_id": subnet["VpcId"],
                "cidr_block": subnet.get("CidrBlock"),
                "availability_zone": subnet.get("AvailabilityZone"),
                "availability_zone_id": subnet.get("AvailabilityZoneId"),
                "available_ip_address_count": subnet.get("AvailableIpAddressCount"),
                "state": subnet.get("State"),
                "map_public_ip_on_launch": subnet.get("MapPublicIpOnLaunch", False),
                "default_for_az": subnet.get("DefaultForAz", False),
                "tags": self._extract_tags(subnet.get("Tags", [])),
                "name": self._get_name_from_tags(subnet.get("Tags", [])),
                "region": self.region,
                "resource_type": self.resource_type.value,
                "raw": subnet,
            }
            normalized_subnets.append(normalized_subnet)

        return normalized_subnets

    def _extract_tags(self, tags: List[Dict[str, str]]) -> Dict[str, str]:
        """Extract tags into a dictionary."""
        return {tag["Key"]: tag["Value"] for tag in tags}

    def _get_name_from_tags(self, tags: List[Dict[str, str]]) -> str:
        """Get the Name tag value."""
        for tag in tags:
            if tag.get("Key") == "Name":
                return tag.get("Value", "")
        return ""
