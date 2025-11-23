"""
VPN Connection collector.

Collects VPN connection resources for hybrid cloud network visualization
and analysis of site-to-site VPN connectivity.
"""

from typing import Any, Dict, List, Optional

from src.collectors.base import BaseCollector
from src.core.constants import ResourceType
from src.core.logging import get_logger

logger = get_logger(__name__)


class VPNConnectionCollector(BaseCollector):
    """
    Collector for AWS VPN Connection resources.

    VPN connections enable secure connectivity between AWS and on-premises
    networks or between AWS regions. Critical for hybrid cloud architectures.
    """

    def __init__(
        self,
        region: str,
        profile: Optional[str] = None,
        rate_limit: Optional[float] = None,
    ):
        """
        Initialize VPN Connection collector.

        Args:
            region: AWS region
            profile: AWS profile
            rate_limit: Rate limit in requests/second
        """
        super().__init__(region, profile, rate_limit)

    @property
    def resource_type(self) -> ResourceType:
        """Resource type for this collector."""
        return ResourceType.VPN_CONNECTION

    @property
    def service_name(self) -> str:
        """AWS service name."""
        return "ec2"

    async def collect_resources(self) -> List[Dict[str, Any]]:
        """
        Collect VPN Connection resources.

        Returns:
            List of VPN connection dictionaries with normalized structure

        Raises:
            CollectorException: If collection fails
        """
        client = self.get_client()

        # Collect VPN connections
        vpn_connections = await self._paginated_call(
            client=client,
            method_name="describe_vpn_connections",
            result_key="VpnConnections",
        )

        # Normalize VPN connection data
        normalized_vpns = []
        for vpn in vpn_connections:
            options = vpn.get("Options", {})
            vgw_telemetry = vpn.get("VgwTelemetry", [])
            routes = vpn.get("Routes", [])

            # Parse tunnel information
            tunnel_info = []
            for tunnel in vgw_telemetry:
                tunnel_info.append({
                    "outside_ip_address": tunnel.get("OutsideIpAddress"),
                    "status": tunnel.get("Status"),
                    "last_status_change": tunnel.get("LastStatusChange").isoformat()
                    if tunnel.get("LastStatusChange")
                    else None,
                    "status_message": tunnel.get("StatusMessage"),
                    "accepted_route_count": tunnel.get("AcceptedRouteCount"),
                    "certificate_arn": tunnel.get("CertificateArn"),
                })

            # Parse routes
            parsed_routes = []
            for route in routes:
                parsed_routes.append({
                    "destination_cidr_block": route.get("DestinationCidrBlock"),
                    "source": route.get("Source"),
                    "state": route.get("State"),
                })

            normalized_vpn = {
                "id": vpn["VpnConnectionId"],
                "state": vpn.get("State"),
                "type": vpn.get("Type"),  # ipsec.1
                "category": vpn.get("Category"),  # VPN or VPN-Classic
                # Gateway information
                "customer_gateway_id": vpn.get("CustomerGatewayId"),
                "vpn_gateway_id": vpn.get("VpnGatewayId"),
                "transit_gateway_id": vpn.get("TransitGatewayId"),
                "core_network_arn": vpn.get("CoreNetworkArn"),
                "core_network_attachment_arn": vpn.get("CoreNetworkAttachmentArn"),
                # Configuration
                "customer_gateway_configuration": vpn.get("CustomerGatewayConfiguration"),
                "static_routes_only": options.get("StaticRoutesOnly"),
                "local_ipv4_network_cidr": options.get("LocalIpv4NetworkCidr"),
                "remote_ipv4_network_cidr": options.get("RemoteIpv4NetworkCidr"),
                "local_ipv6_network_cidr": options.get("LocalIpv6NetworkCidr"),
                "remote_ipv6_network_cidr": options.get("RemoteIpv6NetworkCidr"),
                "enable_acceleration": options.get("EnableAcceleration"),
                "tunnel_inside_ip_version": options.get("TunnelInsideIpVersion"),
                # Tunnel information
                "tunnel_info": tunnel_info,
                "routes": parsed_routes,
                # Metadata
                "tags": self._extract_tags(vpn.get("Tags", [])),
                "name": self._get_name_from_tags(vpn.get("Tags", [])),
                "region": self.region,
                "resource_type": self.resource_type.value,
                # Enhanced metadata for enterprise analysis
                "is_available": vpn.get("State") == "available",
                "tunnel_count": len(vgw_telemetry),
                "active_tunnel_count": len([t for t in vgw_telemetry if t.get("Status") == "UP"]),
                "route_count": len(routes),
                "is_accelerated": options.get("EnableAcceleration", False),
                "uses_transit_gateway": vpn.get("TransitGatewayId") is not None,
                "all_tunnels_up": all(t.get("Status") == "UP" for t in vgw_telemetry),
                "raw": vpn,
            }
            normalized_vpns.append(normalized_vpn)

        logger.info(
            f"Collected {len(normalized_vpns)} VPN Connections in {self.region}",
            extra={
                "count": len(normalized_vpns),
                "region": self.region,
            },
        )

        return normalized_vpns

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
