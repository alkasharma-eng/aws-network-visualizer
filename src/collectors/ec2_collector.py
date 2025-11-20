"""
EC2 instance collector.
"""

from typing import Any, Dict, List, Optional

from src.collectors.base import BaseCollector
from src.core.constants import ResourceType
from src.core.logging import get_logger

logger = get_logger(__name__)


class EC2Collector(BaseCollector):
    """
    Collector for AWS EC2 instance resources.
    """

    def __init__(
        self,
        region: str,
        profile: Optional[str] = None,
        rate_limit: Optional[float] = None,
        vpc_id: Optional[str] = None,
        subnet_id: Optional[str] = None,
    ):
        """
        Initialize EC2 collector.

        Args:
            region: AWS region
            profile: AWS profile
            rate_limit: Rate limit in requests/second
            vpc_id: Optional VPC ID to filter instances
            subnet_id: Optional Subnet ID to filter instances
        """
        super().__init__(region, profile, rate_limit)
        self.vpc_id = vpc_id
        self.subnet_id = subnet_id

    @property
    def resource_type(self) -> ResourceType:
        """Resource type for this collector."""
        return ResourceType.EC2_INSTANCE

    @property
    def service_name(self) -> str:
        """AWS service name."""
        return "ec2"

    async def collect_resources(self) -> List[Dict[str, Any]]:
        """
        Collect EC2 instance resources.

        Returns:
            List of EC2 instance dictionaries with normalized structure

        Raises:
            CollectorException: If collection fails
        """
        client = self.get_client()

        # Build filters
        filters = []
        if self.vpc_id:
            filters.append({"Name": "vpc-id", "Values": [self.vpc_id]})
        if self.subnet_id:
            filters.append({"Name": "subnet-id", "Values": [self.subnet_id]})

        # Collect instances with pagination
        kwargs = {}
        if filters:
            kwargs["Filters"] = filters

        reservations = await self._paginated_call(
            client=client,
            method_name="describe_instances",
            result_key="Reservations",
            **kwargs,
        )

        # Extract instances from reservations and normalize
        normalized_instances = []
        for reservation in reservations:
            for instance in reservation.get("Instances", []):
                normalized_instance = {
                    "id": instance["InstanceId"],
                    "instance_type": instance.get("InstanceType"),
                    "state": instance.get("State", {}).get("Name"),
                    "vpc_id": instance.get("VpcId"),
                    "subnet_id": instance.get("SubnetId"),
                    "private_ip": instance.get("PrivateIpAddress"),
                    "public_ip": instance.get("PublicIpAddress"),
                    "availability_zone": instance.get("Placement", {}).get(
                        "AvailabilityZone"
                    ),
                    "security_groups": [
                        {
                            "id": sg.get("GroupId"),
                            "name": sg.get("GroupName"),
                        }
                        for sg in instance.get("SecurityGroups", [])
                    ],
                    "network_interfaces": self._extract_network_interfaces(
                        instance.get("NetworkInterfaces", [])
                    ),
                    "tags": self._extract_tags(instance.get("Tags", [])),
                    "name": self._get_name_from_tags(instance.get("Tags", [])),
                    "launch_time": instance.get("LaunchTime"),
                    "platform": instance.get("Platform"),
                    "architecture": instance.get("Architecture"),
                    "region": self.region,
                    "resource_type": self.resource_type.value,
                    "raw": instance,
                }
                normalized_instances.append(normalized_instance)

        return normalized_instances

    def _extract_network_interfaces(
        self, interfaces: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Extract network interface information.

        Args:
            interfaces: List of network interface dictionaries

        Returns:
            List of normalized network interface data
        """
        result = []
        for interface in interfaces:
            result.append(
                {
                    "id": interface.get("NetworkInterfaceId"),
                    "subnet_id": interface.get("SubnetId"),
                    "vpc_id": interface.get("VpcId"),
                    "private_ip": interface.get("PrivateIpAddress"),
                    "public_ip": interface.get("Association", {}).get("PublicIp"),
                    "status": interface.get("Status"),
                    "security_groups": [
                        sg.get("GroupId") for sg in interface.get("Groups", [])
                    ],
                }
            )
        return result

    def _extract_tags(self, tags: List[Dict[str, str]]) -> Dict[str, str]:
        """Extract tags into a dictionary."""
        if not tags:
            return {}
        return {tag["Key"]: tag["Value"] for tag in tags}

    def _get_name_from_tags(self, tags: List[Dict[str, str]]) -> str:
        """Get the Name tag value."""
        if not tags:
            return ""
        for tag in tags:
            if tag.get("Key") == "Name":
                return tag.get("Value", "")
        return ""
