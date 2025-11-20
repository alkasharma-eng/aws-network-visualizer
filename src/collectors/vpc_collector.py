"""
VPC resource collector.
"""

from typing import Any, Dict, List

from src.collectors.base import BaseCollector
from src.core.constants import ResourceType
from src.core.logging import get_logger

logger = get_logger(__name__)


class VPCCollector(BaseCollector):
    """
    Collector for AWS VPC resources.
    """

    @property
    def resource_type(self) -> ResourceType:
        """Resource type for this collector."""
        return ResourceType.VPC

    @property
    def service_name(self) -> str:
        """AWS service name."""
        return "ec2"

    async def collect_resources(self) -> List[Dict[str, Any]]:
        """
        Collect VPC resources.

        Returns:
            List of VPC dictionaries with normalized structure

        Raises:
            CollectorException: If collection fails
        """
        client = self.get_client()

        # Collect VPCs with pagination
        vpcs = await self._paginated_call(
            client=client,
            method_name="describe_vpcs",
            result_key="Vpcs",
        )

        # Normalize VPC data
        normalized_vpcs = []
        for vpc in vpcs:
            normalized_vpc = {
                "id": vpc["VpcId"],
                "cidr_block": vpc.get("CidrBlock"),
                "state": vpc.get("State"),
                "is_default": vpc.get("IsDefault", False),
                "dhcp_options_id": vpc.get("DhcpOptionsId"),
                "instance_tenancy": vpc.get("InstanceTenancy"),
                "tags": self._extract_tags(vpc.get("Tags", [])),
                "name": self._get_name_from_tags(vpc.get("Tags", [])),
                "region": self.region,
                "resource_type": self.resource_type.value,
                "raw": vpc,  # Keep raw data for advanced analysis
            }
            normalized_vpcs.append(normalized_vpc)

        return normalized_vpcs

    def _extract_tags(self, tags: List[Dict[str, str]]) -> Dict[str, str]:
        """
        Extract tags into a dictionary.

        Args:
            tags: List of tag dictionaries

        Returns:
            Dictionary of tag key-value pairs
        """
        return {tag["Key"]: tag["Value"] for tag in tags}

    def _get_name_from_tags(self, tags: List[Dict[str, str]]) -> str:
        """
        Get the Name tag value.

        Args:
            tags: List of tag dictionaries

        Returns:
            Name tag value or empty string
        """
        for tag in tags:
            if tag.get("Key") == "Name":
                return tag.get("Value", "")
        return ""
