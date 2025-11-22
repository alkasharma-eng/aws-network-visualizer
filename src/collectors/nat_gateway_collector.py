"""
NAT Gateway collector.

Collects NAT Gateway resources with enterprise-scale optimizations
including pagination, batch processing, and comprehensive error handling.
"""

from typing import Any, Dict, List, Optional

from src.collectors.base import BaseCollector
from src.core.constants import ResourceType
from src.core.logging import get_logger

logger = get_logger(__name__)


class NATGatewayCollector(BaseCollector):
    """
    Collector for AWS NAT Gateway resources.

    NAT Gateways enable instances in private subnets to connect to the internet
    or other AWS services while preventing the internet from initiating connections
    to those instances.
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
        Initialize NAT Gateway collector.

        Args:
            region: AWS region
            profile: AWS profile
            rate_limit: Rate limit in requests/second
            vpc_id: Optional VPC ID to filter NAT gateways
            subnet_id: Optional Subnet ID to filter NAT gateways
        """
        super().__init__(region, profile, rate_limit)
        self.vpc_id = vpc_id
        self.subnet_id = subnet_id

    @property
    def resource_type(self) -> ResourceType:
        """Resource type for this collector."""
        return ResourceType.NAT_GATEWAY

    @property
    def service_name(self) -> str:
        """AWS service name."""
        return "ec2"

    async def collect_resources(self) -> List[Dict[str, Any]]:
        """
        Collect NAT Gateway resources.

        Returns:
            List of NAT Gateway dictionaries with normalized structure

        Raises:
            CollectorException: If collection fails
        """
        client = self.get_client()

        # Build filters for efficient querying
        filters = []
        if self.vpc_id:
            filters.append({"Name": "vpc-id", "Values": [self.vpc_id]})
        if self.subnet_id:
            filters.append({"Name": "subnet-id", "Values": [self.subnet_id]})

        # Filter to only get available NAT gateways (exclude deleted/deleting)
        filters.append({"Name": "state", "Values": ["available", "pending"]})

        # Collect NAT gateways with pagination
        kwargs = {}
        if filters:
            kwargs["Filters"] = filters

        nat_gateways = await self._paginated_call(
            client=client,
            method_name="describe_nat_gateways",
            result_key="NatGateways",
            **kwargs,
        )

        # Normalize NAT gateway data for enterprise-scale processing
        normalized_ngws = []
        for ngw in nat_gateways:
            addresses = ngw.get("NatGatewayAddresses", [])

            normalized_ngw = {
                "id": ngw["NatGatewayId"],
                "vpc_id": ngw.get("VpcId"),
                "subnet_id": ngw.get("SubnetId"),
                "state": ngw.get("State"),
                "connectivity_type": ngw.get("ConnectivityType", "public"),  # public or private
                "nat_gateway_addresses": [
                    {
                        "allocation_id": addr.get("AllocationId"),
                        "network_interface_id": addr.get("NetworkInterfaceId"),
                        "private_ip": addr.get("PrivateIp"),
                        "public_ip": addr.get("PublicIp"),
                        "association_id": addr.get("AssociationId"),
                        "is_primary": addr.get("IsPrimary", False),
                    }
                    for addr in addresses
                ],
                "public_ips": [addr.get("PublicIp") for addr in addresses if addr.get("PublicIp")],
                "private_ips": [addr.get("PrivateIp") for addr in addresses if addr.get("PrivateIp")],
                "network_interface_ids": [
                    addr.get("NetworkInterfaceId") for addr in addresses if addr.get("NetworkInterfaceId")
                ],
                "create_time": ngw.get("CreateTime").isoformat() if ngw.get("CreateTime") else None,
                "delete_time": ngw.get("DeleteTime").isoformat() if ngw.get("DeleteTime") else None,
                "failure_code": ngw.get("FailureCode"),
                "failure_message": ngw.get("FailureMessage"),
                "tags": self._extract_tags(ngw.get("Tags", [])),
                "name": self._get_name_from_tags(ngw.get("Tags", [])),
                "region": self.region,
                "resource_type": self.resource_type.value,
                "raw": ngw,
            }
            normalized_ngws.append(normalized_ngw)

        logger.info(
            f"Collected {len(normalized_ngws)} NAT Gateways in {self.region}",
            extra={
                "count": len(normalized_ngws),
                "region": self.region,
                "vpc_filter": self.vpc_id,
            },
        )

        return normalized_ngws

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
