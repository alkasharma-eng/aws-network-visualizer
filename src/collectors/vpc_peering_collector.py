"""
VPC Peering Connection collector.

Collects VPC peering connections for cross-VPC network visualization
and analysis in enterprise multi-VPC architectures.
"""

from typing import Any, Dict, List, Optional

from src.collectors.base import BaseCollector
from src.core.constants import ResourceType
from src.core.logging import get_logger

logger = get_logger(__name__)


class VPCPeeringCollector(BaseCollector):
    """
    Collector for AWS VPC Peering Connection resources.

    VPC peering connections enable routing of traffic between VPCs using
    private IP addresses. Critical for multi-VPC and multi-account architectures.
    """

    def __init__(
        self,
        region: str,
        profile: Optional[str] = None,
        rate_limit: Optional[float] = None,
        vpc_id: Optional[str] = None,
    ):
        """
        Initialize VPC Peering collector.

        Args:
            region: AWS region
            profile: AWS profile
            rate_limit: Rate limit in requests/second
            vpc_id: Optional VPC ID to filter peering connections
        """
        super().__init__(region, profile, rate_limit)
        self.vpc_id = vpc_id

    @property
    def resource_type(self) -> ResourceType:
        """Resource type for this collector."""
        return ResourceType.VPC_PEERING

    @property
    def service_name(self) -> str:
        """AWS service name."""
        return "ec2"

    async def collect_resources(self) -> List[Dict[str, Any]]:
        """
        Collect VPC Peering Connection resources.

        Returns:
            List of VPC peering dictionaries with normalized structure

        Raises:
            CollectorException: If collection fails
        """
        client = self.get_client()

        # Build filters
        filters = []
        if self.vpc_id:
            # Get peerings where this VPC is either requester or accepter
            filters.append({"Name": "requester-vpc-info.vpc-id", "Values": [self.vpc_id]})

        # Collect VPC peering connections
        kwargs = {}
        if filters:
            kwargs["Filters"] = filters

        peering_connections = await self._paginated_call(
            client=client,
            method_name="describe_vpc_peering_connections",
            result_key="VpcPeeringConnections",
            **kwargs,
        )

        # If vpc_id filter was used, also get connections where VPC is accepter
        if self.vpc_id:
            accepter_connections = await self._paginated_call(
                client=client,
                method_name="describe_vpc_peering_connections",
                result_key="VpcPeeringConnections",
                Filters=[{"Name": "accepter-vpc-info.vpc-id", "Values": [self.vpc_id]}],
            )
            # Merge and deduplicate
            seen_ids = {pc["VpcPeeringConnectionId"] for pc in peering_connections}
            for pc in accepter_connections:
                if pc["VpcPeeringConnectionId"] not in seen_ids:
                    peering_connections.append(pc)

        # Normalize VPC peering data
        normalized_peerings = []
        for peering in peering_connections:
            status = peering.get("Status", {})
            requester_info = peering.get("RequesterVpcInfo", {})
            accepter_info = peering.get("AccepterVpcInfo", {})

            normalized_peering = {
                "id": peering["VpcPeeringConnectionId"],
                "status": status.get("Code"),
                "status_message": status.get("Message"),
                # Requester VPC information
                "requester_vpc_id": requester_info.get("VpcId"),
                "requester_owner_id": requester_info.get("OwnerId"),
                "requester_region": requester_info.get("Region"),
                "requester_cidr_block": requester_info.get("CidrBlock"),
                "requester_cidr_block_set": [
                    cidr.get("CidrBlock") for cidr in requester_info.get("CidrBlockSet", [])
                ],
                "requester_ipv6_cidr_block_set": [
                    cidr.get("Ipv6CidrBlock") for cidr in requester_info.get("Ipv6CidrBlockSet", [])
                ],
                "requester_peering_options": requester_info.get("PeeringOptions", {}),
                # Accepter VPC information
                "accepter_vpc_id": accepter_info.get("VpcId"),
                "accepter_owner_id": accepter_info.get("OwnerId"),
                "accepter_region": accepter_info.get("Region"),
                "accepter_cidr_block": accepter_info.get("CidrBlock"),
                "accepter_cidr_block_set": [
                    cidr.get("CidrBlock") for cidr in accepter_info.get("CidrBlockSet", [])
                ],
                "accepter_ipv6_cidr_block_set": [
                    cidr.get("Ipv6CidrBlock") for cidr in accepter_info.get("Ipv6CidrBlockSet", [])
                ],
                "accepter_peering_options": accepter_info.get("PeeringOptions", {}),
                # Metadata
                "expiration_time": peering.get("ExpirationTime").isoformat() if peering.get("ExpirationTime") else None,
                "tags": self._extract_tags(peering.get("Tags", [])),
                "name": self._get_name_from_tags(peering.get("Tags", [])),
                "region": self.region,
                "resource_type": self.resource_type.value,
                # Enhanced metadata for enterprise analysis
                "is_active": status.get("Code") == "active",
                "is_cross_region": requester_info.get("Region") != accepter_info.get("Region"),
                "is_cross_account": requester_info.get("OwnerId") != accepter_info.get("OwnerId"),
                "connected_vpc_ids": [requester_info.get("VpcId"), accepter_info.get("VpcId")],
                "raw": peering,
            }
            normalized_peerings.append(normalized_peering)

        logger.info(
            f"Collected {len(normalized_peerings)} VPC Peering Connections in {self.region}",
            extra={
                "count": len(normalized_peerings),
                "region": self.region,
                "vpc_filter": self.vpc_id,
            },
        )

        return normalized_peerings

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
