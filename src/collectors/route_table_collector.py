"""
Route Table collector.

Collects Route Table resources with comprehensive route analysis
for enterprise-scale network visualization.
"""

from typing import Any, Dict, List, Optional

from src.collectors.base import BaseCollector
from src.core.constants import ResourceType
from src.core.logging import get_logger

logger = get_logger(__name__)


class RouteTableCollector(BaseCollector):
    """
    Collector for AWS Route Table resources.

    Route tables contain a set of rules (routes) that determine where
    network traffic from your subnet or gateway is directed.
    """

    def __init__(
        self,
        region: str,
        profile: Optional[str] = None,
        rate_limit: Optional[float] = None,
        vpc_id: Optional[str] = None,
    ):
        """
        Initialize Route Table collector.

        Args:
            region: AWS region
            profile: AWS profile
            rate_limit: Rate limit in requests/second
            vpc_id: Optional VPC ID to filter route tables
        """
        super().__init__(region, profile, rate_limit)
        self.vpc_id = vpc_id

    @property
    def resource_type(self) -> ResourceType:
        """Resource type for this collector."""
        return ResourceType.ROUTE_TABLE

    @property
    def service_name(self) -> str:
        """AWS service name."""
        return "ec2"

    async def collect_resources(self) -> List[Dict[str, Any]]:
        """
        Collect Route Table resources.

        Returns:
            List of Route Table dictionaries with normalized structure

        Raises:
            CollectorException: If collection fails
        """
        client = self.get_client()

        # Build filters
        filters = []
        if self.vpc_id:
            filters.append({"Name": "vpc-id", "Values": [self.vpc_id]})

        # Collect route tables with pagination
        kwargs = {}
        if filters:
            kwargs["Filters"] = filters

        route_tables = await self._paginated_call(
            client=client,
            method_name="describe_route_tables",
            result_key="RouteTables",
            **kwargs,
        )

        # Normalize route table data
        normalized_rts = []
        for rt in route_tables:
            routes = rt.get("Routes", [])
            associations = rt.get("Associations", [])

            # Parse routes for network analysis
            parsed_routes = []
            for route in routes:
                parsed_route = {
                    "destination_cidr_block": route.get("DestinationCidrBlock"),
                    "destination_ipv6_cidr_block": route.get("DestinationIpv6CidrBlock"),
                    "destination_prefix_list_id": route.get("DestinationPrefixListId"),
                    "gateway_id": route.get("GatewayId"),
                    "nat_gateway_id": route.get("NatGatewayId"),
                    "transit_gateway_id": route.get("TransitGatewayId"),
                    "local_gateway_id": route.get("LocalGatewayId"),
                    "carrier_gateway_id": route.get("CarrierGatewayId"),
                    "network_interface_id": route.get("NetworkInterfaceId"),
                    "instance_id": route.get("InstanceId"),
                    "vpc_peering_connection_id": route.get("VpcPeeringConnectionId"),
                    "egress_only_internet_gateway_id": route.get("EgressOnlyInternetGatewayId"),
                    "state": route.get("State"),
                    "origin": route.get("Origin"),  # CreateRouteTable, CreateRoute, EnableVgwRoutePropagation
                }
                parsed_routes.append(parsed_route)

            # Parse associations
            parsed_associations = []
            main_route_table = False
            associated_subnet_ids = []

            for assoc in associations:
                is_main = assoc.get("Main", False)
                if is_main:
                    main_route_table = True

                parsed_assoc = {
                    "association_id": assoc.get("RouteTableAssociationId"),
                    "subnet_id": assoc.get("SubnetId"),
                    "gateway_id": assoc.get("GatewayId"),
                    "main": is_main,
                    "association_state": assoc.get("AssociationState", {}).get("State"),
                }
                parsed_associations.append(parsed_assoc)

                if assoc.get("SubnetId"):
                    associated_subnet_ids.append(assoc["SubnetId"])

            normalized_rt = {
                "id": rt["RouteTableId"],
                "vpc_id": rt.get("VpcId"),
                "owner_id": rt.get("OwnerId"),
                "is_main": main_route_table,
                "routes": parsed_routes,
                "associations": parsed_associations,
                "associated_subnet_ids": associated_subnet_ids,
                "propagating_vgws": rt.get("PropagatingVgws", []),
                "tags": self._extract_tags(rt.get("Tags", [])),
                "name": self._get_name_from_tags(rt.get("Tags", [])),
                "region": self.region,
                "resource_type": self.resource_type.value,
                # Enhanced metadata for enterprise analysis
                "route_count": len(routes),
                "association_count": len(associations),
                "has_igw_route": any(r.get("GatewayId", "").startswith("igw-") for r in routes),
                "has_nat_route": any(r.get("NatGatewayId") for r in routes),
                "has_tgw_route": any(r.get("TransitGatewayId") for r in routes),
                "has_peering_route": any(r.get("VpcPeeringConnectionId") for r in routes),
                "raw": rt,
            }
            normalized_rts.append(normalized_rt)

        logger.info(
            f"Collected {len(normalized_rts)} Route Tables in {self.region}",
            extra={
                "count": len(normalized_rts),
                "region": self.region,
                "vpc_filter": self.vpc_id,
            },
        )

        return normalized_rts

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
