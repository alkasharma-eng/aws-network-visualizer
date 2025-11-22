"""
Transit Gateway collector.

Collects Transit Gateway resources and attachments with comprehensive
analysis for enterprise-scale multi-VPC and hybrid cloud architectures.
"""

from typing import Any, Dict, List, Optional

from src.collectors.base import BaseCollector
from src.core.constants import ResourceType
from src.core.logging import get_logger

logger = get_logger(__name__)


class TransitGatewayCollector(BaseCollector):
    """
    Collector for AWS Transit Gateway resources.

    Transit Gateways act as a regional virtual router for connecting VPCs
    and on-premises networks. Critical for enterprise hub-and-spoke architectures.
    """

    def __init__(
        self,
        region: str,
        profile: Optional[str] = None,
        rate_limit: Optional[float] = None,
    ):
        """
        Initialize Transit Gateway collector.

        Args:
            region: AWS region
            profile: AWS profile
            rate_limit: Rate limit in requests/second
        """
        super().__init__(region, profile, rate_limit)

    @property
    def resource_type(self) -> ResourceType:
        """Resource type for this collector."""
        return ResourceType.TRANSIT_GATEWAY

    @property
    def service_name(self) -> str:
        """AWS service name."""
        return "ec2"

    async def collect_resources(self) -> List[Dict[str, Any]]:
        """
        Collect Transit Gateway resources with attachments.

        Returns:
            List of Transit Gateway dictionaries with normalized structure

        Raises:
            CollectorException: If collection fails
        """
        client = self.get_client()

        # Collect transit gateways
        tgws = await self._paginated_call(
            client=client,
            method_name="describe_transit_gateways",
            result_key="TransitGateways",
        )

        # Collect all attachments in parallel for efficiency
        all_attachments = await self._paginated_call(
            client=client,
            method_name="describe_transit_gateway_attachments",
            result_key="TransitGatewayAttachments",
        )

        # Collect route tables for each TGW
        all_route_tables = await self._paginated_call(
            client=client,
            method_name="describe_transit_gateway_route_tables",
            result_key="TransitGatewayRouteTables",
        )

        # Group attachments by TGW ID for efficient lookup
        attachments_by_tgw = {}
        for attachment in all_attachments:
            tgw_id = attachment.get("TransitGatewayId")
            if tgw_id not in attachments_by_tgw:
                attachments_by_tgw[tgw_id] = []
            attachments_by_tgw[tgw_id].append(attachment)

        # Group route tables by TGW ID
        route_tables_by_tgw = {}
        for rt in all_route_tables:
            tgw_id = rt.get("TransitGatewayId")
            if tgw_id not in route_tables_by_tgw:
                route_tables_by_tgw[tgw_id] = []
            route_tables_by_tgw[tgw_id].append(rt)

        # Normalize transit gateway data
        normalized_tgws = []
        for tgw in tgws:
            tgw_id = tgw["TransitGatewayId"]
            options = tgw.get("Options", {})
            attachments = attachments_by_tgw.get(tgw_id, [])
            route_tables = route_tables_by_tgw.get(tgw_id, [])

            # Parse attachments
            parsed_attachments = []
            vpc_attachments = []
            vpn_attachments = []
            direct_connect_attachments = []
            peering_attachments = []

            for attachment in attachments:
                resource_type = attachment.get("ResourceType")
                parsed_attachment = {
                    "attachment_id": attachment.get("TransitGatewayAttachmentId"),
                    "resource_type": resource_type,
                    "resource_id": attachment.get("ResourceId"),
                    "resource_owner_id": attachment.get("ResourceOwnerId"),
                    "state": attachment.get("State"),
                    "association": attachment.get("Association", {}),
                    "tags": self._extract_tags(attachment.get("Tags", [])),
                }
                parsed_attachments.append(parsed_attachment)

                # Categorize by type
                if resource_type == "vpc":
                    vpc_attachments.append(parsed_attachment)
                elif resource_type == "vpn":
                    vpn_attachments.append(parsed_attachment)
                elif resource_type == "direct-connect-gateway":
                    direct_connect_attachments.append(parsed_attachment)
                elif resource_type == "peering":
                    peering_attachments.append(parsed_attachment)

            normalized_tgw = {
                "id": tgw_id,
                "owner_id": tgw.get("OwnerId"),
                "state": tgw.get("State"),
                "description": tgw.get("Description"),
                "creation_time": tgw.get("CreationTime").isoformat() if tgw.get("CreationTime") else None,
                # Options for enterprise configuration
                "amazon_side_asn": options.get("AmazonSideAsn"),
                "auto_accept_shared_attachments": options.get("AutoAcceptSharedAttachments"),
                "default_route_table_association": options.get("DefaultRouteTableAssociation"),
                "default_route_table_propagation": options.get("DefaultRouteTablePropagation"),
                "vpn_ecmp_support": options.get("VpnEcmpSupport"),
                "dns_support": options.get("DnsSupport"),
                "multicast_support": options.get("MulticastSupport"),
                "association_default_route_table_id": options.get("AssociationDefaultRouteTableId"),
                "propagation_default_route_table_id": options.get("PropagationDefaultRouteTableId"),
                # Attachments
                "attachments": parsed_attachments,
                "vpc_attachments": vpc_attachments,
                "vpn_attachments": vpn_attachments,
                "direct_connect_attachments": direct_connect_attachments,
                "peering_attachments": peering_attachments,
                "attached_vpc_ids": [att.get("resource_id") for att in vpc_attachments],
                # Route tables
                "route_tables": [
                    {
                        "route_table_id": rt.get("TransitGatewayRouteTableId"),
                        "default_association_route_table": rt.get("DefaultAssociationRouteTable"),
                        "default_propagation_route_table": rt.get("DefaultPropagationRouteTable"),
                        "state": rt.get("State"),
                        "tags": self._extract_tags(rt.get("Tags", [])),
                    }
                    for rt in route_tables
                ],
                "tags": self._extract_tags(tgw.get("Tags", [])),
                "name": self._get_name_from_tags(tgw.get("Tags", [])),
                "region": self.region,
                "resource_type": self.resource_type.value,
                # Enhanced metadata for enterprise analysis
                "total_attachments": len(attachments),
                "vpc_attachment_count": len(vpc_attachments),
                "vpn_attachment_count": len(vpn_attachments),
                "dx_attachment_count": len(direct_connect_attachments),
                "peering_attachment_count": len(peering_attachments),
                "route_table_count": len(route_tables),
                "raw": tgw,
            }
            normalized_tgws.append(normalized_tgw)

        logger.info(
            f"Collected {len(normalized_tgws)} Transit Gateways with {len(all_attachments)} attachments in {self.region}",
            extra={
                "tgw_count": len(normalized_tgws),
                "attachment_count": len(all_attachments),
                "region": self.region,
            },
        )

        return normalized_tgws

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
